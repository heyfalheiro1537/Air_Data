import os
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
CHROMA_DIR = os.getenv("CHROMA_DIR", "/app/chroma")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "docs")


def build_retriever():
    # Uses OllamaEmbeddings so you don’t depend on any external provider
    embeddings = OllamaEmbeddings(model=OLLAMA_EMBED_MODEL, base_url=OLLAMA_BASE_URL)
    vectordb = Chroma(
        persist_directory=CHROMA_DIR,
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
    )
    return vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 4})
