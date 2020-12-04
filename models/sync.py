from pydantic import BaseModel


class Message(BaseModel):
    session_id: str
    content: str
