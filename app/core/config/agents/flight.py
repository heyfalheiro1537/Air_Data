from app.core.models.interface.chat_agent import BaseChatModule

tools = []


class FlightAgent(BaseChatModule):
    def __init__(self):
        prompt = (
            "Você é um agente especializado em dados de voos."
            + "Seu objetivo é ajudar os usuários a encontrar informações sobre voos, aeroportos, companhias aéreas e outros dados relacionados a viagens aéreas."
            + "Você tem acesso a uma variedade de ferramentas para buscar essas informações."
        )
        super().__init__(tools=tools, prompt=prompt, name="Agente de Voos")
