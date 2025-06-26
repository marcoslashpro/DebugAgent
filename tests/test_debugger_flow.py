from debug_agent.debugger_flow import run_debugger, graph, State, debugger
from debug_agent import DebugAgent, Model, create_logger

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph

import pytest
from unittest.mock import patch, MagicMock
from types import TracebackType


logger = create_logger(__name__)


STATE = State(
  agent=DebugAgent(Model(), error=MagicMock()),
  messages=[],
  traceback=MagicMock(spec=TracebackType)
)


@patch('debug_agent.agent.DebugAgent.interaction', return_value=None, side_effect=None)
def test_debugger_message_format(mock_interaction):
  agent = STATE['agent']
  agent.model.messages.extend(
    [
      AIMessage(content='this is a test'),
      HumanMessage(content='this is a test query')
    ]
  )

  messages = debugger(STATE)['messages']
  logger.debug(f'messages: {messages}')
  logger.debug(f"Agent's model messages: {agent.model.messages}")


  assert len(messages) == len(agent.model.messages)