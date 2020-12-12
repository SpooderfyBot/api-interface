from .gateway import Gateway, gateway_connect


class GatewayException(Exception):
    """ Base gateway exception class"""


class RoomUnknown(GatewayException):
    """ Used for when the gateway returns 404 """


class BadRequest(GatewayException):
    """ Used for when the gateway returns 400 """


class UnknownException(GatewayException):
    """ Used for when the gateway returns 5xx codes """
