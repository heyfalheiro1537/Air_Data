from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.graph import MessagesState
from langgraph.types import Command, Send
from langchain_core.messages import AIMessage, ToolMessage


def create_handoff_tool(*, agent_name: str, description: str | None = None):
    name = f"transfer_to_{agent_name}"
    description = (
        description
        or f"Ferramenta para transferir a conversa para o agente {agent_name}."
    )

    @tool(name, description=description)
    def handoff_tool(
        task_description: Annotated[
            str,
            "Descrição que todo o agente deve fazer, incluindo detalhes e pedindo para ser conciso.",
        ],
        state: Annotated[MessagesState, InjectedState],
    ) -> Command:
        msg = {"role": "user", "content": task_description}
        agent_input = {
            **state,
            "messages": state["messages"] + [msg],
        }
        tool_call_id = None
        for m in reversed(state["messages"]):
            if isinstance(m, AIMessage) and m.tool_calls:
                tool_call_id = m.tool_calls[-1]["id"]
                break
        if tool_call_id is None:
            # fallback defensivo
            tool_call_id = "handoff"

        # 3) Criar o ToolMessage que fecha o ciclo da tool
        tool_msg = ToolMessage(
            content=f"Encaminhando para {agent_name}.",
            name=name,
            tool_call_id=tool_call_id,
        )
        return Command(
            update={"messages": [tool_msg]},
            goto=[Send(agent_name, agent_input)],
            graph=Command.PARENT,
        )

    return handoff_tool
