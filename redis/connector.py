import typing as t

import aioredis


class RedisManager:
    """
    This manages all the redis systems to make is easy to dynamically create
    cache stores without having to manually make a new attr every time.
    """
    def __init__(self, collections: t.List[str]):
        self._pools: t.Dict[str, aioredis.Redis] = {}
        self._collections = collections

    async def setup(self):
        """
        Sets up all the pools by awaiting the connection with `i` being the number of the pool,
        changing the order of the stores will affect the pool.
        :return:
        """
        for i, coll in enumerate(self._collections, start=1):
            self._pools[coll] = await aioredis.create_redis_pool(f"redis://redis:6379/{i}")
            print(f"[ REDIS ][ STATUS ] Created pool {coll}")

    async def shutdown(self):
        for name, pool in self._pools.items():
            print(f"[ REDIS ][ STATUS ] Shutting down pool {name}...")
            pool.close()
            await pool.wait_closed()

    def __getitem__(self, item) -> aioredis.Redis:
        print(self._pools, item)
        return self._pools[item]


redis: RedisManager = None


def create_cache_engine(collections: t.List[str]):
    global redis
    redis = RedisManager(collections)
    print(redis._collections)


async def create_cache():
    global redis
    await redis.setup()
