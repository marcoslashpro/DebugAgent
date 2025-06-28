from debug_agent.agent import parse_thinking_from_response
from functools import partial

import pytest


parse_thinking = partial(parse_thinking_from_response, log_thoughts=False)


def test_parse_response_sucess():
  test_thoughts = """
  <think>This is my testing thought process</think>
  """
  test_response_content = "This is the real response"
  test_response = test_thoughts + test_response_content

  parsed = parse_thinking(test_response)

  assert parsed
  assert parsed == test_response_content


def assert_parse_response_throws_without_response():
  no_response_response = "<think>This should throw ValueError</think>"

  with pytest.raises(ValueError):
    parse_thinking(no_response_response)


def test_parse_response_success_if_no_thoughts():
  no_thoughts_response = "I do not think"
  response = parse_thinking(no_thoughts_response)

  assert response == no_thoughts_response
