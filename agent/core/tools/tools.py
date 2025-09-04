def create_tools():
    pass


# here we are going to define tool

# @tool("sparql_query", return_direct=False)
# def sparql_query(query: str) -> str:
#     """Run a SPARQL SELECT/ASK/DESCRIBE/CONSTRUCT against the local RDFLib store.
#     Input: SPARQL string."""
#     try:
#         qres = rdf_graph.query(query)
#         # Convert result to a readable string
#         if qres.type == "ASK":
#             return str(bool(qres.askAnswer))
#         elif qres.type == "CONSTRUCT":
#             g = Graph()
#             for t in qres.graph.triples((None, None, None)):
#                 g.add(t)
#             return g.serialize(format="turtle").decode("utf-8")
#         else:
#             # SELECT or DESCRIBE falls here via rdflib behavior (DESCRIBE often returns a Graph)
#             if hasattr(qres, "vars"):  # SELECT-like
#                 headers = [str(v) for v in qres.vars]
#                 rows = []
#                 for row in qres:
#                     rows.append([str(val) if val is not None else "" for val in row])
#                 # simple TSV
#                 out = "\t".join(headers) + "\n"
#                 out += "\n".join("\t".join(r) for r in rows)
#                 return out
#             else:
#                 # fallback: try graph serialization
#                 try:
#                     return qres.serialize(format="turtle").decode("utf-8")
#                 except Exception:
#                     return str(list(qres))
#     except Exception as e:
#         return f"SPARQL error: {e}"


# @tool("sql_query", return_direct=False)
# def sql_query(sql: str) -> str:
#     """Run a read-only SQL query against the relational DB. Input: SQL string (SELECT only)."""
#     try:
#         sql_lower = sql.strip().lower()
#         if not sql_lower.startswith("select"):
#             return "Only SELECT queries are allowed in this tool."
#         with engine.connect() as conn:
#             rs = conn.execute(text(sql))
#             rows = rs.mappings().all()
#             if not rows:
#                 return "[]"
#             # format as TSV
#             headers = list(rows[0].keys())
#             out = "\t".join(headers) + "\n"
#             for r in rows:
#                 out += "\t".join([str(r[h]) for h in headers]) + "\n"
#             return out.strip()
#     except Exception as e:
#         return f"SQL error: {e}"
