from fastapi import responses

import router


class PlayerEndpoints(router.Blueprint):
    def __init__(self, app):
        self.app = app

    @router.endpoint(
        "/api/player/{player_id:int}/pause",
        endpoint_name="Pause Player",
        description="Used to pause a set player",
        methods=["PUT"],
    )
    async def pause_player(self, player_id: int):
        print(player_id)
        return responses.ORJSONResponse({"status": 200, "message": "OK"})

    @router.endpoint(
        "/api/player/{player_id:int}/play",
        endpoint_name="Play the player",
        description="Used to start a set player",
        methods=["PUT"],
    )
    async def pause_player(self, player_id: int):
        print(player_id)
        return responses.ORJSONResponse({"status": 200, "message": "OK"})

    @router.endpoint(
        "/api/player/{player_id:int}/next",
        endpoint_name="Next Video",
        description="Cycles to the next item in a playlist",
        methods=["PUT"],
    )
    async def pause_player(self, player_id: int):
        print(player_id)
        return responses.ORJSONResponse({"status": 200, "message": "OK"})

    @router.endpoint(
        "/api/player/{player_id:int}/prev",
        endpoint_name="Previous Video",
        description="Cycles to the previous item in a playlist",
        methods=["PUT"],
    )
    async def pause_player(self, player_id: int):
        print(player_id)
        return responses.ORJSONResponse({"status": 200, "message": "OK"})


class MessageChat(router.Blueprint):
    def __init__(self, app):
        self.app = app

    @router.endpoint(
        "/api/room/{room_id:int}/message",
        endpoint_name="Send Message",
        description="Send a message to the set chat room.",
        methods=["PUT"],
    )
    async def pause_player(self, room_id: str):
        print(room_id)
        return responses.ORJSONResponse({"status": 200, "message": "OK"})


def setup(app):
    app.add_blueprint(PlayerEndpoints(app))
    app.add_blueprint(MessageChat(app))
