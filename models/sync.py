from pydantic import BaseModel


class Message(BaseModel):
    content: str


class Video(BaseModel):
    video_title: str
    video_url: str
