from pydantic import BaseModel


class Message(BaseModel):
    content: str


class Video(BaseModel):
    title: str
    url: str
