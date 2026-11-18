# Ops Agent: an AI agent with human approval

A small Python agent that answers operations requests ("status of billing-api", "restart billing-api")
by letting an LLM choose tools. State-changing actions require human approval.

## What it demonstrates
- Tool use / agentic workflow (LLM picks a tool, the code executes it)
- Human-in-the-loop approval gate and least privilege (read-only tools run freely)
- Input validation (strict service-name pattern, bounded integers)
- Graceful failure (unknown tools, bad args, unparseable model output, step limit)
- Logging of every request, tool call, denial and failure
- Unit tests with pytest (11 cases)

## Run
    pip install -r requirements.txt
    python main.py                      # offline mock LLM
    ANTHROPIC_API_KEY=... python main.py   # real LLM (model via OPS_AGENT_MODEL)
    python -m pytest

## Structure
- `ops_agent/tools.py`  tools, validation, in-memory environment
- `ops_agent/llm.py`    MockLLM (offline) and ClaudeLLM (Anthropic API)
- `ops_agent/agent.py`  agent loop, approval gate, logging
- `tests/`              pytest tests
