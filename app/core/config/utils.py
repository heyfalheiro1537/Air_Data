from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.messages import convert_to_messages

seen_tool_calls = []  # chamadas de tool (nome/args/id)
seen_tool_returns = []  # retornos de tool (conteúdo)


def run_graph(supervisor, payload):
    for chunk in supervisor.stream(payload, subgraphs=True):
        ns, update = chunk if isinstance(chunk, tuple) else (None, chunk)
        for node_name, node_update in update.items():
            msgs = convert_to_messages(node_update["messages"])
            for m in msgs:
                # LLM deciding to call a tool (the "query" intent)
                if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
                    for tc in m.tool_calls:
                        seen_tool_calls.append(
                            {
                                "node": node_name,
                                "name": tc["name"],
                                "args": tc["args"],
                                "id": tc["id"],
                            }
                        )
                # Tool finished and returned a result
                elif isinstance(m, ToolMessage):
                    seen_tool_returns.append(
                        {
                            "node": node_name,
                            "name": m.name,
                            "tool_call_id": m.tool_call_id,
                            "content": m.content,
                        }
                    )
                # Supervisor’s final answer usually lands as an AIMessage with no tool_calls
                elif isinstance(m, AIMessage) and not getattr(m, "tool_calls", None):
                    final_answer = m.content  # keep last one
    return final_answer


def pretty_print_message(message, indent=False):
    pretty_message = message.pretty_repr(html=True)
    if not indent:
        print(pretty_message)
        return

    indented = "\n".join("\t" + c for c in pretty_message.split("\n"))
    print(indented)


def pretty_print_messages(update, last_message=False):
    is_subgraph = False
    if isinstance(update, tuple):
        ns, update = update
        # skip parent graph updates in the printouts
        if len(ns) == 0:
            return

        graph_id = ns[-1].split(":")[0]
        print(f"Update from subgraph {graph_id}:")
        print("\n")
        is_subgraph = True

    for node_name, node_update in update.items():
        update_label = f"Update from node {node_name}:"
        if is_subgraph:
            update_label = "\t" + update_label

        print(update_label)
        print("\n")

        messages = convert_to_messages(node_update["messages"])
        if last_message:
            messages = messages[-1:]

        for m in messages:
            pretty_print_message(m, indent=is_subgraph)
        print("\n")
