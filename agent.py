"""Agent loop: the LLM picks a tool, risky tools wait for human approval, everything is logged."""
import logging

from .tools import ToolError

log = logging.getLogger("ops_agent")


class Agent:
    def __init__(self, llm, tools, approver, max_steps=4):
        self.llm, self.tools, self.approver, self.max_steps = llm, tools, approver, max_steps

    def run(self, request):
        log.info("request: %s", request)
        history = []
        for step in range(self.max_steps):
            decision = self.llm.decide(request, history, self.tools)
            if "final" in decision:
                log.info("final answer after %d step(s)", step)
                return decision["final"]

            name, args = decision.get("tool"), decision.get("args", {})
            tool = self.tools.get(name)
            if tool is None:
                log.warning("model asked for unknown tool: %r", name)
                history.append({"tool": name, "error": "unknown tool"})
                continue

            # Human-in-the-loop: state-changing tools need explicit approval.
            if tool.requires_approval and not self.approver(name, args):
                log.info("approval denied for %s %s", name, args)
                return f"Action '{name}' was not approved. No changes were made."

            try:
                result = tool.func(**args)
                log.info("tool %s ok", name)
                history.append({"tool": name, "args": args, "result": result})
            except (ToolError, TypeError) as exc:
                log.warning("tool %s failed: %s", name, exc)
                history.append({"tool": name, "args": args, "error": str(exc)})
        return "Stopped: reached the step limit without finishing."
