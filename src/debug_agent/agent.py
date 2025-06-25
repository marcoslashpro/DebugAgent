from pdb import Pdb
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, SystemMessage

from debug_agent import create_logger


logger = create_logger(__name__)


class Model:
  def __init__(self, system_prompt: str, model_id: str = "Qwen/Qwen2.5-Coder-7B-Instruct", temperature: int = 0):
    self.model_id = model_id
    self.temperature = temperature
    self.system_prompt = system_prompt
    self.messages: list[BaseMessage] = [
      SystemMessage(self.system_prompt),
    ]

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
    response = self.coder.invoke(messages)
    self.messages.append(AIMessage(content=response.content))

    logger.info(f"Got back response of: {response}")
    return response.content

  def add_message(self, msg: str) -> None:
    self.messages.append(HumanMessage(content=msg))
    logger.info(f"New message added, full conversation: {self.messages}")


class DebugAgent(Pdb):
  def __init__(
    self,
    model: Model,
    complete_key='tab',
    skip=None,
    no_sig_int=False,
    read_rc=True
  ) -> None:

    # --- New Parameters --- #
    self.model = model
    self.messages: list[str] = []

    # --- Pdb Initializations and params --- #
    self.botframe = None
    super().__init__(completekey=complete_key, stdin=None, stdout=None, skip=skip,
                     nosigint=no_sig_int, readrc=read_rc)

  def message(self, msg: str) -> None:
    """
    Override the original message helper function in order to append each message to the message list
    :param msg: The output from the Pdb
    :return: None
    """
    self.messages.append(msg)

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
    return super().postcmd(stop, line)
