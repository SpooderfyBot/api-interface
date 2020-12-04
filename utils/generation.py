from uuid import uuid4


def create_session_id() -> str:
    """ Creates a random string """
    return str(uuid4()).replace("-", "")

