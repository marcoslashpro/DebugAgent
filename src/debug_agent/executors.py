from typing import Any, Protocol
from smolagents.local_python_executor import LocalPythonExecutor, InterpreterError, DANGEROUS_MODULES, DANGEROUS_FUNCTIONS

from debug_agent.exceptions import DangerousActionError
from debug_agent import create_logger


logger = create_logger(__name__)


ALLOWED_PDB_COMMANDS = [
    # Special Pdb-only Syntax / Features
    ";;",

    # Navigating Code / Stepping
    "n",
    "s",
    "r",
    "c",
    "unt",
    "j",

    # Breakpoints
    "b",
    "tbreak",
    "cl",
    "disable",
    "enable",
    "ignore",
    "condition",
    "commands",

    # Inspecting Code and State
    "l",
    "ll",
    "a",
    "p",
    "pp",
    "whatis",
    "source",
    "display",
    "undisplay",
    "interact",

    # Stack Navigation
    "w",
    "u",
    "d",

    # Miscellaneous / Control
    "h",
    "alias",
    "unalias",
    "run",
    "q",
    "debug",
    "retval",
    "locs",
    "globals",
    "pdbrc",

    # Convenience variables (prefixed with $)
    "$_frame",
    "$_retval",
    "$_exception",
]


class BaseExecutor(Protocol):
  """
  Protocol for implementing Executors of any type.
  The executor must implement a `__call__` method that returns the parsed code.
  """
  def __call__(self, code_action: str) -> Any:
    """
    :param:

      `code_action`: The code to execute

    :returns:

      This is based on the implementation. It might return None, or a bool flag...

    :raises:

      `InterpreterError`: An error that is uniquely risen when the code generated from the agent is not correct.
    """
    pass


class PdbExecutor():
  def __init__(self, base_executor: BaseExecutor = LocalPythonExecutor([''])) -> None:
    self.base_executor = base_executor

  def sanitize(self, code: str) -> None:
    try:
      self.base_executor(code_action=code)
    except InterpreterError as e:
      context = e.__context__

      if isinstance(context, SyntaxError):
        # We do not want to allow any command that is not within the allowed ones
        if not validate_pdb_commands(code):
          raise DangerousActionError from e


def is_multiple_commands(code: str) -> bool:
  _, sep, after = code.partition(';;')

  if sep == ';;' and after.strip():
    logger.info(f"After is a cmd: {after}")
    return True

  return False


def validate_pdb_commands(code: str):
  if not is_multiple_commands(code):
    return is_valid_pdb_command(code)

  before, _, after = code.partition(';;')

  if not is_multiple_commands(after):
    return is_valid_pdb_command(after)

  while is_multiple_commands(after):
    if not is_valid_pdb_command(after):
      return False
    before, _, after = code.partition(';;')
    logger.info(f"Before: {before}, sep: {_}, after: {after}")

  return True


def is_valid_pdb_command(code: str) -> bool:
  # Extract the first command
  generated_cmd = code.split()[0]

  # Check for the presence of the generated command in the allowed commands
  # Check fot the length of the generate command == the allowed command
  if generated_cmd in ALLOWED_PDB_COMMANDS:
    cmd_index = ALLOWED_PDB_COMMANDS.index(generated_cmd)
    if len(generated_cmd) == len(ALLOWED_PDB_COMMANDS[cmd_index]):
      return True

  return False
