from functools import wraps, partial
from typing import Callable

from debug_agent import create_logger, prompt_manager as pm


logger = create_logger(__name__)


def Agent(f=None, *, model_id: str | None = None, temperature: int | None = None, n_steps: int | None = None) -> Callable:
	"""
	The decorator to use in order to start the agent debugging session.
	:param f: The function to decorate, this shall not be provided
	:param model_id: The id of the model to use, if not provided, defaults internally to "Qwen2.5-7b-Code-Instruct"
	:param temperature: The temperature to set for the model, defaults internally to 0.
	:param n_steps: The number of steps to use for the model, defaults internally to 5.
	"""
	if f is None:
		# Allows decorator to be used with parameters
		return partial(Agent, temperature=temperature, n_steps=n_steps)

	@wraps(f)
	def inner(*args, **kwargs):
		try:
			return f(*args, **kwargs)
		except Exception as e:
			from debug_agent import agent

			# Allow the model to be instantiated based on the parameters provided in the decorator
			if model_id is not None and temperature is not None:
				model = agent.Model(model_id=model_id, temperature=temperature)
			elif temperature is not None:
				model = agent.Model(temperature=temperature)
			elif model_id is not None:
				model = agent.Model(model_id=model_id)
			else:
				model = agent.Model()

			if n_steps is not None:
				debug_agent = agent.DebugAgent(model=model, n_steps=n_steps, error=e)
			else:
				debug_agent = agent.DebugAgent(model=model, error=e)

			debug_agent.interaction(None, e.__traceback__)
			return None
	return inner
