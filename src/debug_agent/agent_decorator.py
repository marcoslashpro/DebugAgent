from functools import wraps
import sys
from typing import Callable

from debug_agent import create_logger, prompt_manager as pm


logger = create_logger(__name__)


def Agent(f, model_id: str | None = None, temperature: int | None = None, n_steps: int | None = None) -> Callable:
	@wraps(f)
	def inner(*args, **kwargs):
		try:
			return f(*args, **kwargs)
		except Exception as e:
			from debug_agent import agent

			if model_id is not None or temperature is not None:
				model = agent.Model(model_id=model_id, temperature=temperature)
			else:
				model = agent.Model()

			if n_steps is not None:
				debug_agent = agent.DebugAgent(model=model, n_steps=n_steps, error=e)
			else:
				debug_agent = agent.DebugAgent(model=model, error=e)

			debug_agent.interaction(None, sys.exc_info()[-1])
			return None
	return inner