# DebugAgent

An MVP of a Python agent-debugger.

This is not by any mean a finished application, but it seems to be working incredebily good as is.

## How to use it

The user experience is straight forward:

Install the PyPi Package:
```
uv add debug_agent
```
That's it for the installation, now you should have a `debug_agent` package from where you can import the agent.

The only thing to keep in mind is that you are going to have to have a HuggingFace API key with permission to run inference with Inference Providers, you can save the token locally on you machine by doing:
```
huggingface-cli login
```
You'll then be prompted to insert the `hf_token`.

The intended use is as a decorator on functions that raise an error, like this:
```
from debug_agent import Agent

@Agent
def some_risky_function():
  return 'hello' / 10
```
Once the function raises an exception, then the decorator will launch the post-mortem analysis of the code.
The Agent will then start interacting with the debugger, using its commands to analyze the error, outputting a summary of the task at the end of the debugging session.

Optionally, you can also provide parameters to the decorator, which allows us to set a `temperature` for the model, the `n_steps` that the agent should take, and the `model_id`, in order to specify a different model.

Keep in mind tho, that for the moment, the only models available are the one that can be used through the ChatHuggingFace Langchain interface.

## Security
When working on an application like this, where we give the agent access to an interactive python script, security is a must.
I have therefore implemented a custom PdbInterpreter, that only allows valid Pdb commands to be exectued, raising a `DangerousActionError` if ever the agent outputs invalid/malicious commands.

## Considerations

For the moment, the agent seems to perform pretty well on minor errors, such as ZeroDivisionErrors, TypeError, ValueErrors, while showcasing the ability to dig into the stacktrace in order to find where the error originated from. I think that, as the prompt improves and, if we get to that point, with some debugging-specific fine-tuning, this could become a valuable application for python developers.

# Happy Coding!
And come back to me, if you find any problems while using the debugger.
