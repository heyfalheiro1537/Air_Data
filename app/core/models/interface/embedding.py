import os
from typing import List, Dict, Any

# Imports para processamento de PDF e embeddings
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.schema import Document

# Imports para Ollama
from langchain_ollama import OllamaEmbeddings


from app.core.models.interface.model import export_model


model = export_model()


class EmbeddingProcessor:
    """Processador de embeddings para documentos de aviação usando Ollama."""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        persist_directory: str = "./chroma_db_ollama",
    ):
        """
        Inicializa o processador com Ollama.

        Args:
            embedding_model: Modelo de embedding do Ollama (nomic-embed-text, mxbai-embed-large)

            chunk_size: Tamanho dos chunks de texto
            chunk_overlap: Sobreposição entre chunks
            persist_directory: Diretório para persistir o banco vetorial
        """
        # Embeddings do Ollama
        self.embeddings = OllamaEmbeddings(model=model)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        self.persist_directory = persist_directory
        self.vectorstore = None

        print(f"Inicializado com modelo de embedding: {model}")

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extrai texto de um arquivo PDF."""
        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            print(f"Erro ao extrair texto do PDF {pdf_path}: {e}")
            return ""

    def process_pdfs(self, pdf_paths: Dict[str, str]) -> List[Document]:
        """
        Processa os PDFs e cria documentos com metadados.

        Args:
            pdf_paths: Dicionário com nome e caminho dos PDFs

        Returns:
            Lista de documentos processados
        """
        documents = []

        for doc_name, pdf_path in pdf_paths.items():
            print(f"Processando {doc_name}...")

            # Verifica se o arquivo existe
            if not os.path.exists(pdf_path):
                print(f"Arquivo não encontrado: {pdf_path}")
                continue

            # Extrai texto do PDF
            text = self.extract_text_from_pdf(pdf_path)
            if not text.strip():
                print(f"Nenhum texto extraído de {pdf_path}")
                continue

            # Divide o texto em chunks
            chunks = self.text_splitter.split_text(text)

            # Cria documentos com metadados
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "source": doc_name,
                        "file_path": pdf_path,
                        "chunk_id": i,
                        "total_chunks": len(chunks),
                        "type": "legal_document",
                    },
                )
                documents.append(doc)

            print(f"{doc_name}: {len(chunks)} chunks criados")

        return documents

    def create_vectorstore(self, documents: List[Document]) -> Chroma:
        """
        Cria ou carrega o banco vetorial com Ollama embeddings.

        Args:
            documents: Lista de documentos para indexar

        Returns:
            Instância do banco vetorial Chroma
        """
        try:
            # Tenta carregar banco existente
            if os.path.exists(self.persist_directory):
                print("Carregando banco vetorial existente...")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                )

                # Adiciona novos documentos se houver
                if documents:
                    print("Adicionando novos documentos...")
                    self.vectorstore.add_documents(documents)
                    self.vectorstore.persist()
                    print(f"Adicionados {len(documents)} novos documentos")
            else:
                # Cria novo banco vetorial
                print("Criando novo banco vetorial com Ollama...")
                print("Isso pode demorar alguns minutos na primeira execução...")

                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory,
                )
                self.vectorstore.persist()
                print(f"Banco vetorial criado com {len(documents)} documentos")

        except Exception as e:
            print(f"Erro ao criar/carregar banco vetorial: {e}")
            print(
                "Verifique se o Ollama está rodando e o modelo de embedding está baixado:"
            )
            raise

        return self.vectorstore

    def search_similar(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Busca documentos similares à query.

        Args:
            query: Consulta de busca
            k: Número de documentos a retornar

        Returns:
            Lista de documentos similares com scores
        """
        if not self.vectorstore:
            raise ValueError("Banco vetorial não inicializado")

        results = self.vectorstore.similarity_search_with_score(query, k=k)

        return [
            {"content": doc.page_content, "metadata": doc.metadata, "score": score}
            for doc, score in results
        ]
