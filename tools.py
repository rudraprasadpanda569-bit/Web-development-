"""Tools the agent can call. Every tool validates its input and fails gracefully."""
import re
from dataclasses import dataclass
from typing import Callable


class ToolError(Exception):
    """Raised for bad input or a failed action; the agent reports it instead of crashing."""


@dataclass
class Tool:
    name: str
    description: str
    func: Callable
    requires_approval: bool = False


class Environment:
    """A tiny in-memory 'infrastructure' so the project runs anywhere."""

    def __init__(self):
        self.services = {"auth-api": "running", "billing-api": "degraded", "search-api": "running"}
        self.logs = {
            "auth-api": ["INFO login ok", "INFO token refreshed"],
            "billing-api": ["ERROR db timeout", "WARN retrying", "ERROR db timeout"],
            "search-api": ["INFO index ready"],
        }

    def _check_service(self, name):
        # Input validation: strict whitelist pattern, then existence check.
        if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9-]{1,32}", name):
            raise ToolError(f"Invalid service name: {name!r}")
        if name not in self.services:
            raise ToolError(f"Unknown service: {name}")
        return name

    def get_service_status(self, service):
        return {"service": self._check_service(service), "status": self.services[service]}

    def get_logs(self, service, lines=10):
        self._check_service(service)
        if not isinstance(lines, int) or not 1 <= lines <= 50:
            raise ToolError("lines must be an integer between 1 and 50")
        return {"service": service, "logs": self.logs[service][-lines:]}

    def restart_service(self, service):
        self._check_service(service)
        self.services[service] = "running"
        return {"service": service, "status": "running", "note": "restarted"}


def build_tools(env: Environment):
    return {
        "get_service_status": Tool("get_service_status", "Read a service's current status (read-only).", env.get_service_status),
        "get_logs": Tool("get_logs", "Read recent log lines of a service (read-only).", env.get_logs),
        # Least privilege: the only state-changing tool needs human approval.
        "restart_service": Tool("restart_service", "Restart a service. Changes state.", env.restart_service, requires_approval=True),
    }
