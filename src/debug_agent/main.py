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

@Agent(temperature=0.1)
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
