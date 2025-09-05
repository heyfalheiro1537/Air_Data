import os
import asyncio
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from pathlib import Path
import logging

# Imports para processamento de PDF e embeddings
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.schema import Document

# Imports para Ollama
from langchain_ollama import OllamaEmbeddings
from langchain_community.chat_models import ChatOllama

# Imports para LangGraph
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
import operator


class EmbeddingProcessor:
    """Processador de embeddings para documentos de aviação usando Ollama."""

    def __init__(
        self,
        embedding_model: str = "nomic-embed-text",  # Modelo de embedding do Ollama
        ollama_base_url: str = "http://localhost:11434",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        persist_directory: str = "./chroma_db_ollama",
    ):
        """
        Inicializa o processador com Ollama.

        Args:
            embedding_model: Modelo de embedding do Ollama (nomic-embed-text, mxbai-embed-large)
            ollama_base_url: URL base do servidor Ollama
            chunk_size: Tamanho dos chunks de texto
            chunk_overlap: Sobreposição entre chunks
            persist_directory: Diretório para persistir o banco vetorial
        """
        # Embeddings do Ollama
        self.embeddings = OllamaEmbeddings(
            model=embedding_model, base_url=ollama_base_url
        )

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        self.persist_directory = persist_directory
        self.vectorstore = None

        print(f"Inicializado com modelo de embedding: {embedding_model}")

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
                    logger.info("Adicionando novos documentos...")
                    self.vectorstore.add_documents(documents)
                    self.vectorstore.persist()
                    logger.info(f"Adicionados {len(documents)} novos documentos")
            else:
                # Cria novo banco vetorial
                logger.info("Criando novo banco vetorial com Ollama...")
                logger.info("Isso pode demorar alguns minutos na primeira execução...")

                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=self.persist_directory,
                )
                self.vectorstore.persist()
                logger.info(f"Banco vetorial criado com {len(documents)} documentos")

        except Exception as e:
            logger.error(f"Erro ao criar/carregar banco vetorial: {e}")
            logger.error(
                "Verifique se o Ollama está rodando e o modelo de embedding está baixado:"
            )
            logger.error(f"ollama pull nomic-embed-text")
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


class OllamaAviationAgent:
    """Agente de aviação usando Ollama para LLM e embeddings."""

    def __init__(
        self,
        pdf_paths: Dict[str, str],
        llm_model: str = "llama3.1",  # ou llama2, mistral, etc.
        embedding_model: str = "nomic-embed-text",
        ollama_base_url: str = "http://localhost:11434",
    ):
        """
        Inicializa o agente com Ollama.

        Args:
            pdf_paths: Dicionário com caminhos dos PDFs
            llm_model: Modelo LLM do Ollama
            embedding_model: Modelo de embedding do Ollama
            ollama_base_url: URL base do servidor Ollama
        """
        self.pdf_paths = pdf_paths
        self.llm_model = llm_model
        self.embedding_model = embedding_model
        self.ollama_base_url = ollama_base_url

        # Inicializa processador de embeddings com Ollama
        self.embedding_processor = OllamaAviationEmbeddingProcessor(
            embedding_model=embedding_model,
            ollama_base_url=ollama_base_url,
            chunk_size=800,
            chunk_overlap=100,
            persist_directory="./aviation_db_ollama",
        )

        # Inicializa LLM do Ollama
        self.llm = ChatOllama(model=llm_model, base_url=ollama_base_url, temperature=0)

        logger.info(f"Inicializado com LLM: {llm_model}, Embedding: {embedding_model}")

        # Processa documentos e cria vectorstore
        self._setup_vectorstore()

        # Define ferramentas
        self._setup_tools()

        # Cria o grafo
        self.graph = self._create_graph()

    def _setup_vectorstore(self):
        """Configura o banco vetorial com os documentos."""
        print("Processando documentos de aviação com Ollama...")
        documents = self.embedding_processor.process_pdfs(self.pdf_paths)
        self.vectorstore = self.embedding_processor.create_vectorstore(documents)
        print(f"Banco vetorial criado com {len(documents)} documentos")

    def _setup_tools(self):
        """Define as ferramentas disponíveis para o agente."""

        @tool
        def buscar_lei_aeronauta(query: str) -> str:
            """
            Busca informações específicas na Lei do Aeronauta.

            Args:
                query: Consulta sobre direitos, deveres ou regulamentações do aeronauta

            Returns:
                Informações relevantes da Lei do Aeronauta
            """
            results = self.embedding_processor.search_similar(query, k=3)
            lei_results = [
                r
                for r in results
                if "Lei do Aeronauta" in r["metadata"].get("source", "")
            ]

            if not lei_results:
                return "Informação não encontrada na Lei do Aeronauta."

            context = ""
            for result in lei_results[:2]:
                context += f"Lei do Aeronauta: {result['content']}\n\n"

            return context.strip()

        @tool
        def buscar_codigo_aeronautica(query: str) -> str:
            """
            Busca informações no Código Brasileiro de Aeronáutica.

            Args:
                query: Consulta sobre regulamentações, infrações ou procedimentos aeronáuticos

            Returns:
                Informações relevantes do Código Brasileiro de Aeronáutica
            """
            results = self.embedding_processor.search_similar(query, k=3)
            codigo_results = [
                r
                for r in results
                if "Código Brasileiro" in r["metadata"].get("source", "")
            ]

            if not codigo_results:
                return "Informação não encontrada no Código Brasileiro de Aeronáutica."

            context = ""
            for result in codigo_results[:2]:
                context += f"Código Brasileiro de Aeronáutica: {result['content']}\n\n"

            return context.strip()

        @tool
        def buscar_geral(query: str) -> str:
            """
            Busca geral em todos os documentos de aviação.

            Args:
                query: Consulta geral sobre legislação aeronáutica

            Returns:
                Informações relevantes de qualquer documento
            """
            results = self.embedding_processor.search_similar(query, k=4)

            if not results:
                return "Nenhuma informação relevante encontrada."

            context = ""
            for result in results:
                source = result["metadata"].get("source", "Documento")
                context += f"{source}: {result['content'][:400]}...\n\n"

            return context.strip()

        self.tools = [buscar_lei_aeronauta, buscar_codigo_aeronautica, buscar_geral]
        self.tool_node = ToolNode(self.tools)

    def _create_graph(self):
        """Cria o grafo do LangGraph."""

        # Prompt otimizado para modelos Ollama
        agent_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """Você é um assistente especializado em legislação aeronáutica brasileira.

Ferramentas disponíveis:
- buscar_lei_aeronauta: Para direitos e deveres dos aeronautas
- buscar_codigo_aeronautica: Para regulamentações e infrações
- buscar_geral: Para buscas gerais na legislação

Instruções:
1. Use a ferramenta mais específica primeiro
2. Sempre cite a fonte das informações
3. Seja preciso e técnico
4. Responda sempre em português brasileiro
5. Se não encontrar informação, seja claro sobre isso

Responda de forma clara e objetiva.""",
                ),
                ("placeholder", "{messages}"),
            ]
        )

        agent_runnable = agent_prompt | self.llm.bind_tools(self.tools)

        def call_agent(state: AviationAgentState):
            """Chama o agente principal."""
            response = agent_runnable.invoke(state)
            return {"messages": [response]}

        def analyze_topic(state: AviationAgentState):
            """Analisa o tópico da consulta."""
            if not state["messages"]:
                return state

            last_message = state["messages"][-1]
            if isinstance(last_message, HumanMessage):
                content = last_message.content.lower()

                if any(
                    word in content
                    for word in [
                        "aeronauta",
                        "piloto",
                        "comissário",
                        "direito",
                        "jornada",
                    ]
                ):
                    topic = "direitos_aeronauta"
                elif any(
                    word in content
                    for word in ["infração", "multa", "penalidade", "sanção"]
                ):
                    topic = "infrações"
                elif any(
                    word in content
                    for word in ["licença", "habilitação", "certificado"]
                ):
                    topic = "licenciamento"
                else:
                    topic = "geral"

                return {**state, "current_topic": topic}

            return state

        # Cria o grafo
        workflow = StateGraph(AviationAgentState)

        # Adiciona nós
        workflow.add_node("analyze", analyze_topic)
        workflow.add_node("agent", call_agent)
        workflow.add_node("tools", self.tool_node)

        # Define fluxo
        workflow.set_entry_point("analyze")
        workflow.add_edge("analyze", "agent")
        workflow.add_conditional_edges(
            "agent", tools_condition, {"tools": "tools", "__end__": END}
        )
        workflow.add_edge("tools", "agent")

        return workflow.compile()

    def query(self, question: str) -> str:
        """
        Processa uma consulta do usuário.

        Args:
            question: Pergunta sobre legislação aeronáutica

        Returns:
            Resposta do agente
        """
        initial_state = AviationAgentState(
            messages=[HumanMessage(content=question)],
            search_context="",
            current_topic="",
        )

        try:
            result = self.graph.invoke(initial_state)

            # Retorna a última mensagem do assistente
            for message in reversed(result["messages"]):
                if isinstance(message, AIMessage):
                    return message.content

            return "Não foi possível processar a consulta."

        except Exception as e:
            logger.error(f"Erro ao processar consulta: {e}")
            return f"Erro: {str(e)}"


# Função para verificar se o Ollama está funcionando
def check_ollama_status(base_url: str = "http://localhost:11434"):
    """Verifica se o Ollama está rodando e quais modelos estão disponíveis."""
    import requests

    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print("✅ Ollama está rodando!")
            print("Modelos disponíveis:")
            for model in models.get("models", []):
                print(f"  - {model['name']}")
            return True
    except:
        pass

    print("❌ Ollama não está rodando!")
    print("Inicie o Ollama com: ollama serve")
    print("Baixe os modelos necessários:")
    print("  ollama pull llama3.1")
    print("  ollama pull nomic-embed-text")
    return False


# Exemplo de uso
def demo_ollama_aviation_agent():
    """Demonstra o uso do agente com Ollama."""

    # Verifica status do Ollama
    if not check_ollama_status():
        return

    # Caminhos dos PDFs
    pdf_paths = {
        "Lei do Aeronauta": "app/core/tools/embedding/seed/Lei_do_Aeronauta.pdf",
        "Código Brasileiro de Aeronáutica": "app/core/tools/embedding/seed/Código_Brasileiro_de_Aeronáutica.pdf",
    }

    # Cria o agente
    print("Inicializando agente de aviação com Ollama...")
    agent = OllamaAviationAgent(
        pdf_paths=pdf_paths,
        llm_model="llama3.1",  # Use o modelo que você tem
        embedding_model="nomic-embed-text",
    )

    # Testes
    test_questions = [
        "Qual é a jornada máxima de trabalho de um piloto?",
        "Quais são as penalidades para voo não autorizado?",
        "Quais são os direitos do aeronauta?",
    ]

    print("\n" + "=" * 60)
    print("DEMONSTRAÇÃO DO AGENTE COM OLLAMA")
    print("=" * 60)

    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. PERGUNTA: {question}")
        print("-" * 50)

        try:
            response = agent.query(question)
            print(f"RESPOSTA:\n{response}")
        except Exception as e:
            print(f"ERRO: {e}")

        print("-" * 50)


if __name__ == "__main__":
    demo_ollama_aviation_agent()
