import sys
from pdb import Pdb

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, SystemMessage

from debug_agent import create_logger, prompt_manager as pm
from smolagents import evaluate_python_code


logger = create_logger(__name__)


class Model:
  """
  Custom wrapper around Langchain ChatHuggingface and HuggingFaceEndpoint.
  This wrapper allows us three main things:
  1. Store the conversation;
  2. Append dynamically the system prompt to the conversation list after the DebugAgent has been created.
  3. Append the model's response to the conversation dynamically.
  """
  def __init__(
    self,
    system_prompt: str | None = None,
    model_id: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
    temperature: int = 0
  ) -> None:
    """
    :param system_prompt: Should be none if the model is used in the DebugAgent. That will take care of formatting the prompt.
    :param model_id: The id of the model to use, defaults to "Qwen/Qwen2.5-Coder-7B-Instruct". If to be overridden, then a coder model is recommended.
    :param temperature: Defaults to 0 since we are doing some pragmatic work.
    """
    self.model_id = model_id
    self.temperature = temperature
    self.system_prompt = system_prompt
    self.messages: list[BaseMessage] = []

  def add_system_prompt_to_messages(self, system_prompt: str) -> None:
    """
    Simple helper function to add the system prompt to the messages list.
    :param system_prompt: The system prompt to be added to the messages list, if using the DebugAgent, this is done automatically.
    :return: None, modifies the messages list internally.
    """
    self.messages.append(
      SystemMessage(
        system_prompt
      )
    )

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
    :param messages: The messages list to be added to the conversation list, this can be either the model's messages or
    messages coming from somewhere else.
    :return: The content of the response.
    """
    response = self.coder.invoke(messages)
    self.messages.append(AIMessage(content=response.content))

    logger.info(f"Got back response of: {response}")
    return response.content

  def add_message(self, msg: str) -> None:
    """
    Helper function to add a message to the conversation list.
    :param msg: The string of the message to be added to the conversation list, the formatting is done internally.
    :return: None, modifies the messages list internally.
    """
    self.messages.append(HumanMessage(content=msg))
    logger.info(f"New message added, full conversation: {self.messages}")


class DebugAgent(Pdb):
  """
  Custom DebugAgent Interface, it inherits from the Pdb Interface.
  Most of the parameters should not be overridden, unless you know what you're doing.
  Example usage:
  >>>
  >>> from debug_agent import DebugAgent, Model
  >>>
  >>> try:
  >>>   some_risky_op()
  >>> except Exception as e:
  >>>   debugger = DebugAgent(
  >>>     model=Model(),
  >>>     error=e,
  >>>   )
  """

  def __init__(
    self,
    model: Model,
    error: Exception,
    n_steps: int = 5,
    complete_key='tab',
    skip=None,
    no_sig_int=False,
    read_rc=True,
  ) -> None:
    """
    :param model: The LLM to use, mainly a wrapper around Langchain ChatHuggingFace.
    :param error: The exception to analyze in the debugger.
    :param n_steps: The maximum number of steps to run the agent for.
    :param complete_key: SHOULD NOT BE OVERRIDDEN.
    :param skip: SHOULD NOT BE OVERRIDDEN.
    :param no_sig_int: SHOULD NOT BE OVERRIDDEN.
    :param read_rc: SHOULD NOT BE OVERRIDDEN.
    """

    # --- New Parameters --- #
    self.model = model
    self.messages: list[str] = []
    self.error = error
    self.n_steps = n_steps

    # --- Initialize model's system prompt --- #
    self.model.add_system_prompt_to_messages(self.initialize_system_prompt(error=error))

    # --- Pdb Initializations and params --- #
    self.botframe = None
    super().__init__(completekey=complete_key, stdin=sys.stdin, stdout=None, skip=skip,
                     nosigint=no_sig_int, readrc=read_rc)


  # --- Overrides --- #

  def message(self, msg: str) -> None:
    """
    Override the original message helper function in order to append each message to the message list
    :param msg: The output from the Pdb
    :return: None
    """
    if not msg.startswith("(Agent)"):
      self.messages.append(msg)
    super().message(msg)


  def precmd(self, line):
    """
    Override the original precmd method in order to implement a custom Python Interpreter.
    Allowing the model to interact with python runtime and possibly the shell is a powerful operation that comes with great risks.
    The Custom Python Interpreter comes from the smolagents package, it allows us to restrict the model's actions and the harm ir maight cause.
    """
    evaluate_python_code(code=''.join([cmd for cmd in self.cmdqueue]))
    return super().precmd(line)

  def postcmd(self, stop: bool, line: str) -> bool:
    """
    Override the original postcmd function in order to run inference on the model after each executed command.
    :param stop: Should not be supplied, this is provided by the state of the Pdb class that the DebugAgent inherits from.
    :param line: Should not be supplied, this is provided by the state of the Pdb class that the DebugAgent inherits from.
    :return: The original call to the postcmd function
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
    return super().postcmd(stop, line)


  # --- Custom Methods --- #
  def initialize_system_prompt(self, error: Exception) -> str:
    """
    We render the model's initial prompt base on the error with which we initialized the agent.
    :param error: The error from which we'll extract useful initial context for the model
    :return: The formatted prompt.
    """
    return pm.render_template(
      'system_prompt.j2',
      name='Jarvis',
      steps=self.n_steps,
      error_name=error.__class__.__name__,
      error_message=str(error),
    )
