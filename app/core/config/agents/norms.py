from app.core.models.data.chat_agent import BaseChatModule

tools = []


class NormAgent(BaseChatModule):
    def __init__(self):
        prompt = (
            "Você é um agente especializado em normas."
            + "Seu objetivo é ajudar os usuários a encontrar informações sobre normas, regulamentos e diretrizes relacionadas a viagens aéreas."
            + "Você tem acesso a uma variedade de ferramentas para buscar essas informações."
        )
        super().__init__(tools=tools, prompt=prompt, name="Agente de Normas")
