import sys
from pdb import Pdb

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, SystemMessage

from debug_agent import create_logger, prompt_manager as pm
from debug_agent.executors import PdbExecutor


logger = create_logger(__name__)


class Model:
  """
  Custom wrapper around Langchain ChatHuggingface and HuggingFaceEndpoint.
  This wrapper allows us three main things:
  1. Store the conversation;
  2. Append dynamically the system prompt to the conversation list after the DebugAgent has been created.
  3. Append the model's response to the conversation dynamically.

  :param:
    `system_prompt`: Should be none if the model is used in the DebugAgent. That will take care of formatting the prompt.
    `model_id`: The id of the model to use, defaults to "Qwen/Qwen2.5-Coder-7B-Instruct". If to be overridden, then a coder model is recommended.
    `temperature`: Defaults to 0 since we are doing some pragmatic work.
    """
  def __init__(
    self,
    model_id: str,
    temperature: int,
    log_thoughts: bool,
    system_prompt: str | None = None,
  ) -> None:
    self.model_id = model_id
    self.temperature = temperature
    self.system_prompt = system_prompt
    self.messages: list[BaseMessage] = []
    self.log_thoughts = log_thoughts

  @property
  def llm(self) -> HuggingFaceEndpoint:
    return HuggingFaceEndpoint(
      model=self.model_id,
      temperature=self.temperature
    )

  @property
  def coder(self) -> ChatHuggingFace:
    return ChatHuggingFace(
      llm=self.llm,
    )

  def chat(self, messages: list[BaseMessage]) -> str:
    """
    Interface to use to chat with the model.
    The main roles of this function are:
    1. Run inference on the model
    2. Append the model's response to the conversation dynamically.

    :param:
        `messages`: The messages list to be added to the conversation list, this can be either the model's messages or
        messages coming from somewhere else.

    :return: 
      The content of the response.
    """
    response = self.coder.invoke(messages)
    self.messages.append(AIMessage(content=response.content))

    logger.info(f"Parsing the model's toughts")
    parsed_response = parse_thinking_from_response(response.content, self.log_thoughts)

    return parsed_response

  def add_message(self, msg: str) -> None:
    """
    Helper function to add a message to the conversation list.

    :param:
      `msg`: The string of the message to be added to the conversation list, the formatting is done internally.

    :return: `None`, modifies the messages list internally.
    """
    self.messages.append(HumanMessage(content=msg))
    logger.info(f"New message added, full conversation: {self.messages}")


class PdbAgent(Pdb):
  """
  Custom DebugAgent Interface, it inherits from the Pdb Interface.
  Most of the parameters should not be overridden, unless you know what you're doing.

  Example usage:

  ```
   from debug_agent import PdbAgent, Model, PdbExecutor
  try:
    some_risky_op()

  except Exception as e:
    debugger = PdbAgent(
      model=Model(),
      error=e,
      n_steps=5,
      executor=PdbExecutor()
     )
    debugger.interaction(None, e.__traceback__)
  ```

  :param:

    `model`: The LLM to use, mainly a wrapper around Langchain ChatHuggingFace.

    `error`: The exception to analyze in the debugger.

    `n_steps`: The maximum number of steps to run the agent for.

    `executor`: The Executor that carries the burden of parsing the model's code.
    Here, a custom PdbExecutor is used.

    `complete_key`: SHOULD NOT BE OVERRIDDEN.

    `skip`: SHOULD NOT BE OVERRIDDEN.

    `no_sig_int`: SHOULD NOT BE OVERRIDDEN.

    `read_rc`: SHOULD NOT BE OVERRIDDEN.
  """

  def __init__(
    self,
    model: Model,
    error: Exception,
    n_steps: int,
    executor: PdbExecutor,
    complete_key='tab',
    skip=None,
    no_sig_int=False,
    read_rc=True,
  ) -> None:
    # --- New Parameters --- #
    self.model: Model = model
    self.messages: list[str] = []
    self.exception: Exception = error
    self.n_steps: int = n_steps
    self.executor = executor

    # --- Initialize model's system prompt --- #
    add_system_prompt_to_messages(self.model.messages, self.initialize_system_prompt(error=error))

    # --- Pdb Initializations and params --- #
    self.botframe = None
    super().__init__(completekey=complete_key, stdin=sys.stdin, stdout=None, skip=skip,
                     nosigint=no_sig_int, readrc=read_rc)


  # --- Overrides --- #
  def message(self, msg: str) -> None:
    """
    Override the original message helper function in order to append each message to the message list

    :param:

      `msg`: The output from the Pdb

    :return: None
    """
    if not msg.startswith("(Agent)"):
      self.messages.append(msg)
    super().message(msg)

  def onecmd(self, line):  # type: ignore[ovveride]
    """
    Overrides the original onecmd method from Pdb.
    The reason being that we want to execute the model's output in a safe environment,
    making sure that no harm is caused to the system.
    Here we take advantage of the executor given in the __init__, that is supposed to parse the model's code
    and forbid illegal actions.
    """
    self.executor.sanitize(code=''.join([cmd for cmd in self.cmdqueue]))
    super().onecmd(line)

  def postcmd(self, stop: bool, line: str) -> bool:
    """
    Override the original postcmd function in order to run inference on the model after each executed command.
    If the last command given by the model is 'q', then we quit the debugger.

    :param:

      `stop`: Should not be supplied, this is provided by the state of the Pdb class that the DebugAgent inherits from.
      `line`: Should not be supplied, this is provided by the state of the Pdb class that the DebugAgent inherits from.

    :return:
      The original call to the postcmd function
    """
    new_message = ''.join(self.messages)
    logger.info(f"New message created: {new_message}")
    self.model.add_message(new_message)

    # Clearing debugger cached messages, to avoid bloating the model's context
    self.messages.clear()

    logger.info(f"Invoking the model")
    response = self.model.chat(self.model.messages)

    logger.info(f"Appending the response to the commands")
    self.cmdqueue.append(response)
    for cmd in self.cmdqueue:
      self.message(f'(Agent) {cmd}')

    if self.cmdqueue is not None and self.cmdqueue[-1] == 'q':
      return super().postcmd(True, line)

    return super().postcmd(False, line)


  # --- Custom Methods --- #
  def initialize_system_prompt(self, error: Exception) -> str:
    """
    We render the model's initial prompt base on the error with which we initialized the agent.

    :param:
      `error`: The error from which we'll extract useful initial context for the model

    :return:
      The formatted prompt.

    :raises:
      `TemplateError`, in case that the template could have not been located or if the arguments are not the right ones.
    """
    return pm.render_template(
      'system_prompt.j2',
      name='Jarvis',
      steps=self.n_steps,
      error_name=error.__class__.__name__,
      error_message=str(error),
    )


def add_system_prompt_to_messages(messages: list[BaseMessage], system_prompt: str) -> None:
  """
  Simple helper function to add the system prompt to the messages list.

  :param:
    `messages`: The messages list to append the system prompt to.
    `system_prompt`: The system prompt to be added to the messages list, if using the DebugAgent, this is done automatically.

  :return:
    `None`, modifies the messages list internally.

  :raises:
    `ValueError`, in case that the messages list is not empty.
  """
  if len(messages) == 0:
    messages.append(
      SystemMessage(
        system_prompt
      )
    )
    return

  raise ValueError(
    f"The messages list should be empty in order to add the system prompt, got {messages}"
  )

def parse_thinking_from_response(response: str, log_thoughts: bool = True) -> str:
  """
  We instruct models to think in XML paragraphs like: <think></think>.
  This function is used to remove that part from the model, and optionally log it.

  :param:

    `response`: The pre-parsed model's response

    `log_thoughts`: a boolean flag to decide if we should log the thinking process or not.

  :return:

    The parsed model's response 

  :raises:

    `ValueError`: If the model's response, after parsing the toughts is empty
  """
  before, sep, after = response.partition('</think>')

  if not sep or not after:
    return before.strip()

  if log_thoughts:
    logger.info(f"The model thought: {before + sep}")

  if not after.strip():
    raise ValueError(
      f"The model failes to generate a valid response, got response of: {after}"
    )

  return after.strip()