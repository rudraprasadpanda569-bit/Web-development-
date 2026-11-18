import pytest

from ops_agent.agent import Agent
from ops_agent.llm import MockLLM
from ops_agent.tools import Environment, ToolError, build_tools


def make_agent(approve):
    env = Environment()
    return env, Agent(MockLLM(), build_tools(env), lambda name, args: approve)


def test_read_only_tool_needs_no_approval():
    env, agent = make_agent(approve=False)
    assert "degraded" in agent.run("status of billing-api")


def test_restart_denied_changes_nothing():
    env, agent = make_agent(approve=False)
    assert "not approved" in agent.run("restart billing-api")
    assert env.services["billing-api"] == "degraded"


def test_restart_approved_changes_state():
    env, agent = make_agent(approve=True)
    agent.run("restart billing-api")
    assert env.services["billing-api"] == "running"


@pytest.mark.parametrize("bad", ["../etc", "AUTH", "x" * 40, "", None])
def test_invalid_service_names_rejected(bad):
    with pytest.raises(ToolError):
        Environment().get_service_status(bad)


def test_unknown_service_fails_gracefully():
    _, agent = make_agent(approve=True)
    assert "Unknown service" in agent.run("status of ghost-api")


def test_log_line_limit_validated():
    with pytest.raises(ToolError):
        Environment().get_logs("auth-api", lines=999)


def test_unknown_tool_and_step_limit():
    class BadLLM:
        def decide(self, request, history, tools):
            return {"tool": "delete_everything", "args": {}}

    agent = Agent(BadLLM(), build_tools(Environment()), lambda n, a: True, max_steps=3)
    assert "step limit" in agent.run("anything")
