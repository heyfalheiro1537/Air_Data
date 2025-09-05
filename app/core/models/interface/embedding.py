import os
import hashlib
from typing import List, Dict, Any
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings


EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "airdata_norms")


def _chunk_id(doc_name: str, chunk_text: str) -> str:
    h = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()
    return f"{doc_name}:{h}"


class EmbeddingProcessor:
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        persist_directory: str = "./chroma_db_ollama",
        embedding_model: str = EMBED_MODEL,
    ):
        self.embeddings = OllamaEmbeddings(model=embedding_model)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        self.persist_directory = persist_directory
        self.vectorstore = None
        print(f"[Embeddings] model: {embedding_model}")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        try:
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join((page.extract_text() or "") for page in reader.pages)
        except Exception as e:
            print(f"Erro ao extrair texto do PDF {pdf_path}: {e}")
            return ""

    def process_pdfs(self, pdf_paths: Dict[str, str]) -> List[Document]:
        docs: List[Document] = []
        for doc_name, pdf_path in pdf_paths.items():
            print(f"Processando {doc_name}...")
            if not os.path.exists(pdf_path):
                print(f"Arquivo não encontrado: {pdf_path}")
                continue
            text = self.extract_text_from_pdf(pdf_path)
            if not text.strip():
                print(f"Nenhum texto extraído de {pdf_path}")
                continue
            chunks = self.text_splitter.split_text(text)
            for chunk in chunks:
                docs.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": doc_name,
                            "file_path": pdf_path,
                            "type": "legal_document",
                            "doc_id": _chunk_id(doc_name, chunk),  # ✅ stable ID
                        },
                    )
                )
            print(f"{doc_name}: {len(chunks)} chunks criados")
        return docs

    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        # Always open the same named collection so we can check existing IDs
        self.vectorstore = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
        )

        if not documents:
            return self.vectorstore

        # ✅ only add NEW ids (skip what’s already there)
        all_ids = [d.metadata["doc_id"] for d in documents]
        # query only these ids; returns the ones that already exist
        existing = set(self.vectorstore._collection.get(ids=all_ids).get("ids", []))

        to_add_texts, to_add_metas, to_add_ids = [], [], []
        for d in documents:
            did = d.metadata["doc_id"]
            if did in existing:
                continue
            to_add_texts.append(d.page_content)
            to_add_metas.append(d.metadata)
            to_add_ids.append(did)

        if to_add_texts:
            print(f"Adicionando {len(to_add_texts)} novos chunks…")
            # add in batches to keep memory steady
            B = 10
            for i in range(0, len(to_add_texts), B):
                print(f"Adicionando chunks {i} a {i + B}...")
                self.vectorstore.add_texts(
                    texts=to_add_texts[i : i + B],
                    metadatas=to_add_metas[i : i + B],
                    ids=to_add_ids[i : i + B],
                )

        else:
            print("Nada novo para adicionar (índice já atualizado).")

        return self.vectorstore

    def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        if not self.vectorstore:
            raise ValueError("Banco vetorial não inicializado")
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        return [
            {"content": d.page_content, "metadata": d.metadata, "score": s}
            for d, s in results
        ]
