import os

from langchain_ollama import ChatOllama
# from agent.core.config.system_prompt import SYSTEM_PROMPT
# from agent.core.tools.tools import get_tools

from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import ChatPromptTemplate


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

# set up downloading in docker, now begin test locally


def build_llm() -> ChatOllama:
    return ChatOllama(
        model="gpt-oss:20b", validate_model_on_init=True, temperature=0.8, verbose=True
    )


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


if __name__ == "__main__":
    llm = build_llm()
    response = llm.invoke("What is the capital of France?")
    print(response)
