import sys
import traceback
from smolagents import evaluate_python_code


def raises():
  raise IndexError


if __name__ == "__main__":
  try:
    evaluate_python_code(';;')
  except Exception as e:
    