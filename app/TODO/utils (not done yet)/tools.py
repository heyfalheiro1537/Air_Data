# import os
# from typing import List, Optional


# from langchain_core.tools import tool

# from agent.core.config.triplestore import Triplestore
# from agent.core.tools.utils import build_retriever


def get_tools():
    return []


# def make_sparql_tool(
#     store: Triplestore = Triplestore(),
#     *,
#     read_only: bool = True,
#     default_construct_format: str = "turtle",
#     max_rows: int = 1000,
#     allowed_write_verbs: Optional[List[str]] = None,
# ):
#     """
#     Create a LangChain tool named 'sparql_query'.

#     - SELECT: returns TSV (header + rows), capped at max_rows.
#     - ASK: returns "true"/"false".
#     - CONSTRUCT/DESCRIBE: returns serialized graph (default Turtle).
#     - UPDATE (INSERT/DELETE/...): only if read_only=False and verb allowed.
#     """
#     if allowed_write_verbs is None:
#         # SPARQL 1.1 Update verbs (subset)
#         allowed_write_verbs = [
#             "INSERT",
#             "DELETE",
#             "WITH",
#             "LOAD",
#             "CLEAR",
#             "CREATE",
#             "DROP",
#             "ADD",
#             "MOVE",
#             "COPY",
#         ]

#     def _is_write(q_upper: str) -> bool:
#         return any(q_upper.startswith(verb) for verb in allowed_write_verbs)

#     @tool("sparql_query", return_direct=False)
#     def sparql_query(sparql: str) -> str:
#         try:
#             q = sparql.strip()
#             q_upper = q.upper()

#             # Writes (guarded)
#             if _is_write(q_upper):
#                 if read_only:
#                     return "Write blocked: read-only mode."
#                 store.update(q)
#                 return "OK"

#             # ASK
#             if q_upper.startswith("ASK"):
#                 return "true" if store.ask(q) else "false"

#             # CONSTRUCT / DESCRIBE
#             if q_upper.startswith("CONSTRUCT") or q_upper.startswith("DESCRIBE"):
#                 return store.construct(q, fmt=default_construct_format)

#             # SELECT (default)
#             rows = store.select(q)
#             if not rows:
#                 return "empty"

#             # Enforce row cap
#             rows = rows[:max_rows]

#             headers = list(rows[0].keys())
#             # TSV (header + rows)
#             out = "\t".join(headers) + "\n"
#             out += "\n".join(
#                 "\t".join(str(r.get(h, "")) for h in headers) for r in rows
#             )
#             return out

#         except PermissionError as e:
#             return f"SPARQL permission error: {e}"
#         except Exception as e:
#             return f"SPARQL error: {e}"

#     return sparql_query
