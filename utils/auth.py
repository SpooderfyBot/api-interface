from functools import wraps
from fastapi import Request, responses
from redis import redis


async def session_valid(request: Request) -> bool:
    """ Checks to see if a given request has a valid session """

    session_id = request.cookies.get("session")
    if session_id is None:
        return False

    session = await redis['sessions'].get(session_id)
    return session is not None


def login_required(func):
    """
    A simple decorator that checks the incoming request and makes sure the user
    has got a valid session otherwise forcing them to login and then redirecting
    them back to the endpoint.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")

        session_id = request.cookies.get("session")
        if session_id is None:
            url = request.url
            resp = responses.RedirectResponse(f"/api/login")
            resp.set_cookie("redirect_to", url.path)
            return resp

        session = await redis['sessions'].get(session_id)
        if session is None:
            url = request.url
            resp = responses.RedirectResponse(f"/api/login")
            resp.set_cookie("redirect_to", url.path)
            return resp
        return await func(*args, **kwargs)
    return wrapper



