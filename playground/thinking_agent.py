from debug_agent.agent import Model
from debug_agent import create_logger

from langchain_core.messages import HumanMessage, AIMessage


logger = create_logger(__name__)


model = Model(
  model_id='Qwen/Qwen3-8B'
)


response = model.chat(
  [HumanMessage(content='How can I solve a ZeroDivisionError? Think about it')]
)
