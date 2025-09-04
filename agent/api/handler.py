from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from agent.common.models.ask_body import AskBody
from agent.core.agent import build_agent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = build_agent()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(body: AskBody):
    if not body.question:
        raise HTTPException(400, "question required")
    out = app.state.agent.invoke({"input": body.question})
    return {"answer": out.get("output", "")}
