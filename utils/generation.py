from uuid import uuid4
from string import ascii_uppercase, digits
from random import choices


SELECTION_LETTERS = [*ascii_uppercase, *digits]


def create_session_id() -> str:
    """ Creates a random string """
    return str(uuid4()).replace("-", "")


def create_room_id(k=5) -> str:
    """ Creates a random string where k is the length of the id """
    return "".join(choices(SELECTION_LETTERS, k=k))

