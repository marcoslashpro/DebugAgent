# DebugAgent

A barebone MVP of an agent-based python debugger.
The system is built on top of PDB, the official python debugger.

For the moment, two main things happen:

1. The Output of the Pdb debugger becomes the input of the Agent, and viceversa;
2. The Agent's actions are limited by a custom Python Interpreter(kindly borrowed from the smolagents library), that limits the harm of the Agent.


This is not by any mean a finished application, but it seems to be working incredebily good as is.

## How to use it

The user experience is straight forward:

Clone the package and install(a PyPi version is coming in the future)
```
git clone https://github.com/marcoslashpro/DebugAgent && cd DebugAgent
uv pip install -e .
```
That's it for the installation, now you should a `debug_agent` package from where you can import the agent.

The intended use is as a decorator on the risky function, like this:
```
from debug_agent import DebugAgent

@DebugAgent
def some_risky_function():
  return 'hello' / 10
```
Once the function raises an exception, then the decorator will launch the post-mortem analysis of the code.
The Agent will then start interacting with the debugger, using its commands to analyze the error, outputting a summary of the task at the end of the debugging session.

## Problems:
1. Prompt is quite weak at the moment, the agent might not behave as intended(e.g. returns answer in a wrongly formatted manner). If this happens, the application raises a TypeError, I am looking into the solution, both of the error handling and agent's response format.
