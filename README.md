# Evolution-of-Plan

Let LLM evolves its plan until it works
![Evolution-of-Plan](https://github.com/user-attachments/assets/af98faeb-66d6-4278-af86-67d668d1954e)


To serve a vLLM endpoint, use following command on RunPod instance
```bash
cd tuning && python vllm_serve.py
```
Make sure to expose your target port, record the 'pod_id' and 'model_name' to initialize our 'get_vllm_response_func' through 
```python
from methods.llm import get_vllm_endpoint_func

model_name = "unsloth/Llama-3.2-1B-Instruct"
INTERNAL_PORT = ....
POD_ID = "..."
get_endpoint_response = get_vllm_endpoint_func(model_name, POD_ID, INTERNAL_PORT)
``` 
## Project Setup

The easiest way to set up the development environment is to use the provided Makefile:

```
make install
```

This will automatically create a virtual environment and install the project dependencies.

Alternatively, you can set up the environment manually:

## Virtual Environment Setup

To set up the development environment, first create a virtual environment:

```
python -m venv .venv
```

Then activate the virtual environment:

- On macOS/Linux: `source .venv/bin/activate`

## Project Installation

With the virtual environment activated, install the project dependencies:

```
pip install -e .
```

## Environment Variables

This project requires an API key stored in an `.env` file. Create the `.env` file in the root of the project directory and add the following:

```
OPENAI_API_KEY="xxxxxxxxxxxxxxxx"
ANTHROPIC_API_KEY="xxxxxxxxxxxxxxxx"
GROQ_API_KEY="xxxxxxxxxxxxx"
```

Make sure to never commit the `.env` file to version control, as it contains sensitive information.


## Branching and Pushing Code to Repository

When working on an improvement or feature, please create a new branch with a prefix denoting your name and surname, and then the branch name. For example: `fy/improving_node_evolution`. This way, when you do `git branch -r`, you can see who has what branches open.

When the branch is ready for review, then make a Pull Request (PR) into GitHub and set someone to review it. If it's something trivial, then review it yourself and merge it. Please don't push directly into `main` (this will be blocked soon).

We will add some tests for core module functionality so that we won't be able to push to `main` without passing tests. This is an effort to prevent introducing breaking changes.

I also want to introduce automatic benchmark running so we always know the current score of the `main` branch.