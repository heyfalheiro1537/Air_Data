import os
from typing import Optional, List, Dict, Any

from rdflib import Graph
from rdflib.plugins.stores.sparqlstore import SPARQLStore, SPARQLUpdateStore


class Triplestore:
    """
    Thin wrapper over RDFLib SPARQLStore / SPARQLUpdateStore.
    - SELECT/ASK/CONSTRUCT/DESCRIBE use the query store (read-only).
    - UPDATE uses the update store when available (optional).
    """

    def __init__(
        self, query_url: Optional[str] = None, update_url: Optional[str] = None
    ):
        # Read store
        if not query_url:
            query_url = os.getenv("SPARQL_QUERY_URL")

        self._qstore = SPARQLStore(query_endpoint=query_url)
        self._qgraph = Graph(store=self._qstore)

        # Update store
        if not update_url:
            update_url = os.getenv("SPARQL_UPDATE_URL")
        self._ustore = SPARQLUpdateStore()
        self._ustore.open((query_url, update_url))
        self._ugraph = Graph(store=self._ustore)

    def select(self, query: str) -> List[Dict[str, Any]]:
        """
        Returns a list of dicts with stringified values.
        """
        try:
            results = self._qgraph.query(query)
            # rdflib returns a Result object; rows are tuples aligned with .vars
            headers = [str(v) for v in results.vars]
            rows = []
            for row in results:
                rows.append(
                    {
                        h: (str(val) if val is not None else "")
                        for h, val in zip(headers, row)
                    }
                )
            return rows
        except Exception as e:
            raise RuntimeError(f"SPARQL SELECT error: {e}") from e

    def ask(self, query: str) -> bool:
        try:
            result = self._qgraph.query(query)
            return bool(result.askAnswer)  # rdflib exposes askAnswer for ASK queries
        except Exception as e:
            raise RuntimeError(f"SPARQL ASK error: {e}") from e

    def construct(self, query: str, fmt: str = "turtle") -> str:
        """
        Returns serialized graph (default Turtle) for CONSTRUCT/DESCRIBE.
        """
        try:
            result_graph = Graph()
            for triple in self._qgraph.query(query).graph.triples((None, None, None)):
                result_graph.add(triple)
            return result_graph.serialize(format=fmt).decode("utf-8")
        except Exception as e:
            raise RuntimeError(f"SPARQL CONSTRUCT/DESCRIBE error: {e}") from e

    def update(self, update_stmt: str) -> None:
        """
        Executes INSERT/DELETE updates if an update endpoint is configured.
        """
        if not self._ugraph:
            raise PermissionError("Update endpoint not configured (read-only mode).")
        try:
            self._ugraph.update(update_stmt)
        except Exception as e:
            raise RuntimeError(f"SPARQL UPDATE error: {e}") from e
