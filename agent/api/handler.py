from fastapi import FastAPI
from agent.common.models.ask_body import AskBody


app = FastAPI()


@app.get("/")
def healthcheck():
    return {"status": "ok"}


@app.post("/ask")
def ask(payload: AskBody):
    res = agent_executor.invoke({"input": payload.question})
    return {"answer": res.get("output", "")}
