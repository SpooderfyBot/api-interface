from functools import wraps
from fastapi import Request, responses
from redis import redis


async def session_valid(request: Request) -> bool:
    session_id = request.cookies.get("session")
    if session_id is None:
        return False

    session = await redis['session'].get(session_id)
    return session is not None


def login_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        session_id = request.cookies.get("session")
        if session_id is None:
            url = request.url
            return responses.RedirectResponse(f"/api/login?redirect_to={url}")

        session = await redis['session'].get(session_id)
        if session is None:
            url = request.url
            return responses.RedirectResponse(f"/api/login?redirect_to={url}")
        await func(request, *args, **kwargs)
    return wrapper



