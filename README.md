# Tool Caller Agent

A modular AI agent framework that integrates multiple tools with LLMs (OpenAI, Gemini, etc.) to process user queries, execute tool calls, and return structured responses.

---

## Project Structure

```
Project Structure

├── Makefile
├── README.md
├── requirements.txt
├── src/
│   ├── logs/
│   │   └── app.log
│   ├── tests/
│   └── tool_caller/
│       ├── cli.py
│       ├── config/
│       │   ├── __init__.py
│       │   ├── logging_config.py
│       │   └── settings.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── llm_client.py
│       │   ├── tool_executor.py
│       │   └── tool_registry.py
│       ├── __init__.py
│       ├── main.py
│       ├── models/
│       │   ├── gemini_response.py
│       │   ├── requests.py
│       │   └── responses.py
│       └── tools/
│           ├── base.py
│           ├── calculator_tool.py
│           ├── __init__.py
│           └── registry.py

```

---

### Notes:

- `src/tool_caller/` is the main framework for your tool-calling application.
- `tools/` contains implementations and a registry system that allows adding new tools easily.
- `core/` handles LLM client communication, tool execution, and registry management.
- `config/` stores settings and logging configuration.
- `models/` contains data models for API responses.
- `logs/` stores runtime logs.
- `main.py` in `src` is the entry point for the CLI application.

## Features

- **Tool Registry System**: Register new tools dynamically with metadata (name, description, parameters).
- **LLM Integration**: Supports multiple LLM providers like OpenAI and Gemini.
- **Safe Tool Execution**: Standardized `ToolResponse` with success, error, and execution time.
- **Extensible**: Easily add new tools by inheriting from `BaseTool`.
- **CLI Interface**: Interactive or non-interactive modes for user input.

---

## Setup

1. **Install `uv`** (a virtual environment and task runner):

```bash
pip install uv
```

2. **Create a virtual environment and install dependencies**:

```bash
uv run pip install -r requirements.txt
```

This will read from `requirements.txt` and install all necessary packages.

3. **Move into the source directory**:

```bash
cd src
```

---

## Running the Application

Execute the tool caller:

```bash
uv run python -m tool_caller
```

You will be prompted for a user request. The LLM will process the request and call registered tools if needed. Results and outputs will be printed in the console.

**Interactive Mode** (future support):

```bash
uv run python -m tool_caller --interactive
```

---

## Adding New Tools

1. Create a new tool class inheriting from `BaseTool` in `src/tool_caller/tools/`.

2. Implement `_run` for core logic and optionally override `parameters_model`.

3. Register the tool in `tools/registry.py` with the `register_all_tools` function.

**Example**:

```python
class MyTool(BaseTool):
    @property
    def name(self) -> str:
        return "my_tool"

    @property
    def description(self) -> str:
        return "Example tool"

    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={"type": "object", "properties": {}, "required": []}
        )

    async def _run(self, **kwargs):
        return {"message": "Hello from MyTool!"}
```

---

## Logs

Logs are saved in `src/logs/app.log` by default. Logging is enabled for tool execution, LLM requests, and errors.

---

## Testing

Run tests from `tests` using `pytest`:

```bash
uv run pytest
```

---

## Notes

- Ensure API keys for LLMs are loaded properly in `config/settings.py`.

- `ToolRegistry` ensures no duplicate tools; overwriting logs a warning.

- Currently supports OpenAI and Gemini LLM providers; other providers can be added.

---

## License

MIT License.

# Refactor & Extend: Simple Tool-Using Agent

**Goal:** Turn a brittle, partially working agent into production-quality code, then extend it with a new tool and real tests.

---

## You must **refactor for robustness**, **add one new tool** (translator / unit converter), and **add proper tests**.

## Your Tasks (Summary)

1. **Refactor**
2. **Improve**
3. **Add ONE new tool**
4. **Write tests**
5. **Improve Documentation**

See the assignment brief for full details (shared in the job post).

---

## Quick Start

### Python 3.10+ recommended

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Run

```bash
python main.py "What is 12.5% of 243?"
python main.py "Summarize today's weather in Paris in 3 words"
python main.py "Who is Ada Lovelace?"
python main.py "Add 10 to the average temperature in Paris and London right now."
```

### Test

```bash
pytest -q
```

> Note: The fake LLM sometimes emits malformed JSON to simulate real-world flakiness.

---

## What we expect you to change

- Split responsibilities into modules/classes.
- Add a schema for tool plans; validate inputs and tool names.
- Make tool calls resilient and typed;
- Add one new tool and tests that prove your design is extensible.
- Update this README with an architecture diagram (ASCII ok) and clear instructions.
- You can use Real LLMs or a fake one, but ensure your code is robust against malformed responses.

Good luck & have fun!
