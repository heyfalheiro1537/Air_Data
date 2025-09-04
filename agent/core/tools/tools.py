import os
from typing import List, Optional


from langchain_core.tools import tool

from agent.core.config.connection.triplestore import Triplestore
from agent.core.tools.utils import build_retriever


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHROMA_DIR = os.getenv("CHROMA_DIR", "/app/chroma")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "docs")


def get_tools():
    return [make_retriever_tool(), make_sparql_tool()]


def make_retriever_tool():
    retriever = build_retriever()

    @tool("retrieve_docs", return_direct=False)
    def retrieve_docs(question: str) -> str:
        """Return top-K chunks from the vector store related to the question."""
        docs = retriever.invoke(question)
        if not docs:
            return "no docs"
        parts = []
        for d in docs[:4]:
            meta = d.metadata or {}
            src = meta.get("source") or meta.get("path") or "unknown"
            parts.append(f"[{src}] {d.page_content[:800]}")
        return "\n---\n".join(parts)

    return retrieve_docs


def make_sparql_tool(
    store: Triplestore = Triplestore(),
    *,
    read_only: bool = True,
    default_construct_format: str = "turtle",
    max_rows: int = 1000,
    allowed_write_verbs: Optional[List[str]] = None,
):
    """
    Create a LangChain tool named 'sparql_query'.

    - SELECT: returns TSV (header + rows), capped at max_rows.
    - ASK: returns "true"/"false".
    - CONSTRUCT/DESCRIBE: returns serialized graph (default Turtle).
    - UPDATE (INSERT/DELETE/...): only if read_only=False and verb allowed.
    """
    if allowed_write_verbs is None:
        # SPARQL 1.1 Update verbs (subset)
        allowed_write_verbs = [
            "INSERT",
            "DELETE",
            "WITH",
            "LOAD",
            "CLEAR",
            "CREATE",
            "DROP",
            "ADD",
            "MOVE",
            "COPY",
        ]

    def _is_write(q_upper: str) -> bool:
        return any(q_upper.startswith(verb) for verb in allowed_write_verbs)

    @tool("sparql_query", return_direct=False)
    def sparql_query(sparql: str) -> str:
        try:
            q = sparql.strip()
            q_upper = q.upper()

            # Writes (guarded)
            if _is_write(q_upper):
                if read_only:
                    return "Write blocked: read-only mode."
                store.update(q)
                return "OK"

            # ASK
            if q_upper.startswith("ASK"):
                return "true" if store.ask(q) else "false"

            # CONSTRUCT / DESCRIBE
            if q_upper.startswith("CONSTRUCT") or q_upper.startswith("DESCRIBE"):
                return store.construct(q, fmt=default_construct_format)

            # SELECT (default)
            rows = store.select(q)
            if not rows:
                return "empty"

            # Enforce row cap
            rows = rows[:max_rows]

            headers = list(rows[0].keys())
            # TSV (header + rows)
            out = "\t".join(headers) + "\n"
            out += "\n".join(
                "\t".join(str(r.get(h, "")) for h in headers) for r in rows
            )
            return out

        except PermissionError as e:
            return f"SPARQL permission error: {e}"
        except Exception as e:
            return f"SPARQL error: {e}"

    return sparql_query
