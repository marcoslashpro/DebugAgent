from typing import Iterable, Any

from debug_agent import create_logger, Agent


logger = create_logger(__name__)


def _sum(x: Iterable[Any]) -> int:
	n = 0
	for i in x:
		n += i
	return n

def average(numbers):
	return _sum(numbers) / len(numbers)


@Agent
def main():
	numbers = []
	print("Enter some numbers, enter 'done' when you're done")
	while True:
		number = input("Enter a number: ")
		if number == 'done':
			print(f'The average of the numbers is: {average(numbers)}')
			return
		numbers.append(number)


if __name__ == "__main__":
	print("""
This is an interactive demo of the agent.
There is a bug in the main.py file, I dare you to find it, the agent is pretty good at it.
Now we start:
""")
	main()
