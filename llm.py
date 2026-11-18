"""LLM backends. MockLLM runs offline; ClaudeLLM uses the Anthropic API."""
import json
import os
import re


class MockLLM:
    """Rule-based stand-in so the agent and tests run without an API key."""

    def decide(self, request, history, tools):
        if history:
            last = history[-1]
            if "error" in last:
                return {"final": f"Could not complete the request: {last['error']}"}
            return {"final": f"Done: {json.dumps(last['result'])}"}
        match = re.search(r"[a-z0-9]+(?:-[a-z0-9]+)+", request.lower())
        if not match:
            return {"final": "Please mention a service name, e.g. billing-api."}
        service, text = match.group(0), request.lower()
        if "restart" in text:
            return {"tool": "restart_service", "args": {"service": service}}
        if "log" in text:
            return {"tool": "get_logs", "args": {"service": service}}
        return {"tool": "get_service_status", "args": {"service": service}}


class ClaudeLLM:
    def __init__(self, model=None):
        import anthropic  # imported lazily so the project works without it

        self.client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        self.model = model or os.getenv("OPS_AGENT_MODEL", "claude-sonnet-5-5")

    def decide(self, request, history, tools):
        tool_list = "\n".join(f"- {t.name}: {t.description}" for t in tools.values())
        system = (
            "You are an operations assistant. Available tools:\n" + tool_list +
            '\nReply with ONLY JSON: {"tool": "<name>", "args": {...}} to call a tool, '
            'or {"final": "<answer>"} when done.'
        )
        msg = self.client.messages.create(
            model=self.model, max_tokens=300, system=system,
            messages=[{"role": "user", "content": f"Request: {request}\nHistory: {json.dumps(history)}"}],
        )
        try:
            return json.loads(msg.content[0].text)
        except (json.JSONDecodeError, IndexError):
            return {"final": "Could not parse the model's reply."}  # graceful failure
