from debug_agent.executors import PdbExecutor, ALLOWED_PDB_COMMANDS, is_multiple_commands, is_valid_pdb_command, validate_pdb_commands
from debug_agent.exceptions import DangerousActionError
from smolagents.local_python_executor import InterpreterError

from unittest.mock import MagicMock, patch
import pytest



class MockBaseExecutor:
  """
  We have to mock the side_effect of raising a Interpreter error from a SyntaxError
  """
  def __call__(self, code_action: str) -> None:
    try:
      raise SyntaxError
    except SyntaxError:
      raise InterpreterError


executor = PdbExecutor(base_executor=MockBaseExecutor())


@pytest.mark.parametrize('cmd, expected', [
  ('import', False),
  ('!', False),
  ('wathever', False),
  ('import os', False),
  ('os', False),
  (' import', False),
  ('\nimport', False),
  ('\n\nimport', False),
  ('\n\timport', False),
  ('\timport', False),
  ('  import', False),
  ('l',  True),
  ('c', True),
  ('q', True),
  ('ll', True)
])
def test_is_valid_pdb_cmd(cmd, expected):
  assert is_valid_pdb_command(cmd) == expected


@pytest.mark.parametrize('cmd, expected', [
  ('import', False),
  ('!', False),
  ('wathever', False),
  ('import os', False),
  ('os', False),
  (' import', False),
  ('\timport', False),
  ('  import', False),
  ('l', False),
  ('l;; import', True),
  ('c;; l', True),
  ('p;; c', True)
])
def test_is_multiple_cmds(cmd, expected):
  assert is_multiple_commands(cmd) == expected


@pytest.mark.parametrize('cmd, expected', [
  ('import', False),
  ('!', False),
  ('wathever', False),
  ('import os', False),
  ('os', False),
  (' import', False),
  ('\timport', False),
  ('  import', False),
  ('l',  True),
  ('c', True),
  ('q', True),
  ('ll', True),
  ('l;; import', False),
  ('c;; l', True),
  ('p;; c', True),
  ('p n;; l', True),
  ('l;; p n', True),
  ('p n;; import', False),
  ('import os', False),
  ('p n;; l;; import', False),
  ('l;; os;; p n', False),
  ('builtins', False),
  ('l;; builtins', False),
  ('l ;;   \tbuiltins', False),
])
def test_validate_pdb_cmds(cmd, expected):
  assert validate_pdb_commands(cmd) == expected


@pytest.mark.parametrize('cmd, expected', [
  ('import', False),
  ('!', False),
  ('wathever', False),
  ('import os', False),
  ('os', False),
  (' import', False),
  ('\timport', False),
  ('  import', False),
  ('l;; import', False),
  ('p n;; import', False),
  ('import os', False),
  ('p n;; l;; import', False),
  ('l;; os;; p n', False),
  ('builtins', False),
  ('l;; builtins', False),
  ('l ;;   \tbuiltins', False),
  ('\tos ;; l;; import', False),
  ('__import__', False),
  ('\t.__import__', False),
  ('l;;  \t\tn.__import__', False),
  ('l ;; q;; c;; import;; l', False)
])
def test_executor_validate(cmd, expected):
  with pytest.raises(DangerousActionError):
    executor.sanitize(cmd)