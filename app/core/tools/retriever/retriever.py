# embedding_tool.py
from langchain.tools.retriever import create_retriever_tool

from app.core.models.interface.embedding import EmbeddingProcessor

pdfs = {
    "Código Brasileiro de Aeronáutica": "app/seed/CBA.pdf",
    "Lei do Aeronaute": "app/seed/Lei_do_Aeronauta.pdf",
}


def build_pdf_retriever_tool():
    ep = EmbeddingProcessor()

    docs = ep.process_pdfs(pdfs)  # ingest PDFs (creates Document list)
    vs = ep.create_vectorstore(docs)  # create/load Chroma
    retriever = vs.as_retriever(
        search_kwargs={
            "k": 4,
        }
    )

    tool = create_retriever_tool(
        retriever,
        name="airdata_pdf_search",
        description=(
            "Search aviation PDFs indexed by AirData. "
            "Use this to find exact passages; returns the most relevant chunks. "
            "Cite using metadata.source and, if present, page/chunk info."
        ),
    )
    return tool
