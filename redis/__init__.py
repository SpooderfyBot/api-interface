from .connector import RedisManager, create_cache, create_cache_engine

redis: RedisManager = None


def cache_reload():
    from .connector import redis

    global redis
    redis = redis
