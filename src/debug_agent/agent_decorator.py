from functools import wraps, partial
from typing import Callable

from debug_agent import create_logger
from debug_agent.debugger_flow import run_debugger
from debug_agent.executors import BaseExecutor, PdbExecutor


logger = create_logger(__name__)


def Agent(
		f=None, *,
		model_id: str = 'Qwen/Qwen3-8B',
		temperature: int = 0,
		n_steps: int = 3,
		log_thoughts: bool = False,
		executor: PdbExecutor = PdbExecutor()
	) -> Callable:
	"""
	The decorator to use in order to start the agent debugging session.

	:params:

		`f`: The function to decorate, this shall not be provided

		`model_id`: The id of the model to use, if not provided, defaults to 'Qwen/Qwen3-8B'

		`temperature`: The temperature to set for the model, defaults to 0.

		`log_thoughts`: A boolean flag to decide if the application should log the model's thoughts

		`n_steps`: The max number of steps for the agent in the debugger, defaults to 5.

		`executor`: A executor class that implements a .sanitize method that analyzes the given code and raises a DanguerousActionError if the 
		given code is not defined as safe to execute.
	"""
	if f is None:
		# Allows decorator to be used with parameters
		return partial(Agent, temperature=temperature, n_steps=n_steps)

	@wraps(f)
	def inner(*args, **kwargs):
		try:
			return f(*args, **kwargs)
		except Exception as e:
			if not e.__traceback__:
				raise RuntimeError(
					f"The exception provided does not have a traceback. "
					"In order to launch the Pdb, we need to have access to the exception's traceback. "
					f"The traceback we got is: {e.__traceback__}, please provide it."
				)

			from debug_agent import agent

			# Allow the model to be instantiated based on the parameters provided in the decorator
			model = agent.Model(
				model_id=model_id,
				temperature=temperature,
				log_thoughts=log_thoughts
			)

			debug_agent = agent.PdbAgent(model=model, error=e, n_steps=n_steps, executor=executor)

			response = run_debugger(agent=debug_agent, traceback=e.__traceback__)
			print(response)
			return None

	return inner
