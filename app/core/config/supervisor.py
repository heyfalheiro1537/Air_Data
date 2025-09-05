from sys import path


path.append("./")

from app.core.config.agents.swan import SwanAgent
from app.core.config.agents.weather import WeatherAgent
from app.core.config.agents.norms import NormAgent
from app.core.config.agents.flight import FlightAgent
from app.core.config.system_prompt import SYSTEM_PROMPT
from app.core.models.interface.chat_agent import BaseSupervisorModule

agents = [
    FlightAgent().module,
    NormAgent().module,
    SwanAgent().module,
    WeatherAgent().module,
]


class SupervisorAgent(BaseSupervisorModule):
    def __init__(self):
        prompt = SYSTEM_PROMPT
        super().__init__(agents=agents, prompt=prompt, name="Agente Supervisor")


if __name__ == "__main__":
    supervisor = SupervisorAgent()
    try:
        while True:
            user_input = input("Pergunta: ")
            print(supervisor.call(user_input))
    except KeyboardInterrupt:
        print("\nEncerrando supervisor.")
