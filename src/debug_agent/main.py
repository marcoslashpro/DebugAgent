from functools import wraps
import sys
from typing import Iterable, Any

from debug_agent.prompts import prompt_manager as pm
from debug_agent import create_logger


logger = create_logger(__name__)


def debug_agent(f):
	@wraps(f)
	def inner(*args, **kwargs):
		try:
			return f(*args, **kwargs)
		except Exception as e:
			logger.info(f"Exception caught: {e}")
			e_name, e, e_trace = sys.exc_info()
			from debug_agent import agent
			logger.info(f"Rendering the system prompt")
			sys_prompt = pm.render_template('system_prompt.j2',
												 name='Jarvis', steps=3, error_name=e_name, error_message=e)
			logger.info(f"Instantiating the model")
			model = agent.Model(system_prompt=sys_prompt); debug_agent = agent.DebugAgent(model)
			logger.info(f"Starting the debugging session")
			debug_agent.interaction(None, e_trace)
			return None
	return inner

def _sum(x: Iterable[Any]) -> int:
	n = 0
	for i in x:
		n += i
	return n

def average(numbers):
	return _sum(numbers) / len(numbers)

@debug_agent
def main():
	numbers = []
	while True:
		number = input("You: ")
		if number == 'done':
			print(f'The average of the numbers is: {average(numbers)}')
			return
		numbers.append(number)


if __name__ == "__main__":
	main()
