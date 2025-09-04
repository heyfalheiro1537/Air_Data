import os

from langchain_community.llms import Ollama
from agent.core.config.system_prompt import SYSTEM_PROMPT
from agent.core.tools.tools import get_tools

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import ChatPromptTemplate


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")


def build_llm() -> Ollama:
    return Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)


def build_agent() -> AgentExecutor:
    llm = build_llm()
    tools = get_tools()

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            ("scratchpad", "{agent_scratchpad}"),
        ]
    )

    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)
