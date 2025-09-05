from langchain.tools.retriever import create_retriever_tool
from app.core.models.interface.embedding import EmbeddingProcessor

pdfs = {
    "Código Brasileiro de Aeronáutica": "app/seed/CBA.pdf",
    "Lei do Aeronauta": "app/seed/Lei_do_Aeronauta.pdf",
}


def build_pdf_retriever_tool():
    ep = EmbeddingProcessor(
        embedding_model="nomic-embed-text",
        persist_directory="./chroma_db_ollama",
    )
    docs = ep.process_pdfs(pdfs)
    vs = ep.create_vectorstore(docs)
    retriever = vs.as_retriever(search_kwargs={"k": 4})
    return create_retriever_tool(
        retriever,
        name="consultar_normas_aeronauticas",
        description=(
            "Procurar na documentação normativa. "
            "Use para lookups factuais; retorne passagens relevantes "
            "Cite metadata.source e doc_id."
        ),
    )
