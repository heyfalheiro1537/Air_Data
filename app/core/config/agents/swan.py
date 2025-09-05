from app.core.models.interface.chat_agent import BaseChatModule

tools = []


class SwanAgent(BaseChatModule):
    def __init__(self):
        prompt = (
            "Você é um agente especializado em ocorrências aéreas."
            + "Seu objetivo é ajudar os usuários a encontrar informações sobre ocorrências aéreas."
            + "Você tem acesso a uma variedade de ferramentas para buscar essas informações."
        )
        super().__init__(
            tools=tools, prompt=prompt, name="Agente de Ocorrências Aéreas"
        )
