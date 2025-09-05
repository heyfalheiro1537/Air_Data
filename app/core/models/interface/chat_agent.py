from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
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

    def call(self, input: str) -> str:
        message = {"messages": [{"role": "user", "content": input}]}
        try:
            answer = self.module.invoke(message)
            return answer
        except Exception as e:
            return f"Erro ao processar: {str(e)}"
