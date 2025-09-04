import os
import requests
from typing import Optional, Dict, Any, List

from langchain_community.llms import Ollama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_chroma import Chroma

from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import ChatPromptTemplate


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

CHROMA_DIR = os.getenv("CHROMA_DIR", "/app/chroma")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "docs")

READ_ONLY = os.getenv("READ_ONLY", "true").lower() == "true"


def build_llm() -> Ollama:
    return Ollama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)


def build_retriever():
    # Uses OllamaEmbeddings so you don’t depend on any external provider
    embeddings = OllamaEmbeddings(model=OLLAMA_EMBED_MODEL, base_url=OLLAMA_BASE_URL)
    vectordb = Chroma(
        persist_directory=CHROMA_DIR,
        collection_name=CHROMA_COLLECTION,
        embedding_function=embeddings,
    )
    return vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 4})


def build_agent() -> AgentExecutor:
    llm = build_llm()

    tools = []
    # RAG tool (optional—only if you’ve indexed docs in Chroma)
    retriever = build_retriever()
    tools.append(make_retriever_tool(retriever))

    # SPARQL tool (only if env URL is provided)
    s_tool = make_sparql_tool()
    if s_tool:
        tools.append(s_tool)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            ("human", "{input}"),
            ("scratchpad", "{agent_scratchpad}"),
        ]
    )

    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=False)
