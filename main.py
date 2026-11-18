import logging
import os

from ops_agent.agent import Agent
from ops_agent.llm import ClaudeLLM, MockLLM
from ops_agent.tools import Environment, build_tools


def ask_human(name, args):
    return input(f"Approve {name} {args}? [y/N] ").strip().lower() == "y"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    llm = ClaudeLLM() if os.getenv("ANTHROPIC_API_KEY") else MockLLM()
    agent = Agent(llm, build_tools(Environment()), ask_human)
    while True:
        request = input("\nAsk the ops agent (or 'quit'): ")
        if request.strip().lower() == "quit":
            break
        print(agent.run(request))
