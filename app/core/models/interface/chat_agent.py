from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

from app.core.models.interface.model import export_model


model = export_model()


class BaseChatModule:
    def __init__(self, tools: list = [], prompt: str = "", name: str = ""):
        self.tools = tools
        self.prompt = prompt
        self.name = name
        self.module = create_react_agent(
            model=ChatOllama(model=model),
            tools=tools,
            prompt=prompt,
            name=name,
        )


class BaseSupervisorModule:
    def __init__(self, agents: list = [], prompt: str = "", name: str = ""):
        self.supervisor = create_supervisor(
            model=ChatOllama(model=model),
            agents=agents,
            prompt=prompt,
        ).compile()

    def call(self, input: str) -> str:
        message = {"messages": [{"role": "user", "content": input}]}
        answer = self.supervisor.invoke(message)["messages"][-1].content
        return answer.split("</think>")[-1].strip()
