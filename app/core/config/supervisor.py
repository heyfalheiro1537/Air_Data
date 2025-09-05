from sys import path


path.append("./")
from app.core.config.utils import run_graph
from app.core.tools.supervisor.handoff import create_handoff_tool

from app.core.config.agents.swan import SwanAgent
from app.core.config.agents.weather import WeatherAgent
from app.core.config.agents.norms import NormAgent
from app.core.config.agents.flight import FlightAgent
from app.core.config.system_prompt import SYSTEM_PROMPT
from app.core.models.interface.chat_agent import BaseChatModule

from langgraph.graph import StateGraph, MessagesState, START, END


flight_agent = FlightAgent()
norm_agent = NormAgent()
swan_agent = SwanAgent()
weather_agent = WeatherAgent()

agents: list[BaseChatModule] = [
    flight_agent,
    norm_agent,
    swan_agent,
    weather_agent,
]


handoff_tools = [create_handoff_tool(agent_name=agent.name) for agent in agents]


class SupervisorAgent(BaseChatModule):
    def __init__(self):
        prompt = SYSTEM_PROMPT
        # Passar as ferramentas de transferência para o supervisor
        super().__init__(
            prompt=prompt,
            name="Agente Supervisor",
            tools=handoff_tools,  # Adicionar as ferramentas aqui
        )


supervisor_agent = SupervisorAgent()

supervisor = (
    StateGraph(MessagesState)
    .add_node(
        supervisor_agent.module,
        destinations=(
            norm_agent.name,
            flight_agent.name,
            swan_agent.name,
            weather_agent.name,
            END,
        ),
    )
    .add_node(norm_agent.module)
    .add_node(flight_agent.module)
    .add_node(swan_agent.module)
    .add_node(weather_agent.module)
    .add_edge(START, supervisor_agent.name)
    .add_edge(norm_agent.name, supervisor_agent.name)
    .add_edge(flight_agent.name, supervisor_agent.name)
    .add_edge(swan_agent.name, supervisor_agent.name)
    .add_edge(weather_agent.name, supervisor_agent.name)
    .compile()
)


if __name__ == "__main__":
    print(norm_agent.call("O que é a Lei do Aeronauta?"))
