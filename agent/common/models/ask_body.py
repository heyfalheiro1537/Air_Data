from pydantic import BaseModel


class AskBody(BaseModel):
    session_id: str
    question: str
