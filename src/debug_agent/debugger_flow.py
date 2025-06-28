from debug_agent.agent import PdbAgent
from debug_agent import create_logger

from langgraph.graph import add_messages, StateGraph, START, END

from typing import TypedDict, Annotated
from types import TracebackType


logger = create_logger(__name__)


class State(TypedDict):
  agent: PdbAgent
  messages: Annotated[list, add_messages]
  traceback: TracebackType


def debugger(state: State):
  agent = state['agent']
  traceback = state['traceback']
  logger.debug(f"Gathered from the state: {agent=}, {traceback=}.\nStarting debuggin session...")

  agent.interaction(None, traceback)

  logger.debug(f"Debugging session finished, accumulated messages: {agent.model.messages}")
  return {'messages': agent.model.messages}

def final_answer(state: State):
  agent = state['agent']
  messages = state.get('messages')
  logger.debug(f"Fetched from the state messages: {messages}")

  response = agent.model.chat(messages)

  return {'messages': response}


builder = StateGraph(State)
builder.add_node('debugger', debugger)
builder.add_node('final_answer', final_answer)
builder.add_edge(START, 'debugger')
builder.add_edge('debugger', 'final_answer')
builder.add_edge('final_answer', END)


graph = builder.compile()


def run_debugger(
    agent: PdbAgent,
    traceback: TracebackType
  ) -> str | list[str | dict] | None:

  state = State(
    agent=agent,
    messages=[],
    traceback=traceback
  )

  state['messages'] = agent.model.messages

  state = graph.invoke(state)

  if state.get('messages') and len(state['messages']) > 0:
    last_message = state['messages'][-1]

    return last_message.content