from pydantic import BaseModel
import typing as t


class UserInfoResponse(BaseModel):
    status: int = 200
    exists: bool
    session_id: t.Optional[str] = None

