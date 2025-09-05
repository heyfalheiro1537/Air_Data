from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from core.models.requests.ask_body import AskBody
from app.core.config.supervisor import SupervisorAgent


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = SupervisorAgent()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/ask")
def ask(body: AskBody):
    if not body.question:
        raise HTTPException(400, "question required")
    out = app.state.agent.call(body.question)
    return {"answer": out}
