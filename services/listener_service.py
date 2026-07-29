import os
from collections.abc import AsyncGenerator
from enum import StrEnum

from redis.asyncio import Redis
from redis.client import PubSub
from redis.typing import EncodableT


class Channels(StrEnum):
    EXPORTS = "exports"


class ListenerService:
    _redis: Redis
    _pubsub: PubSub

    def __init__(self):
        self._redis = Redis(
            host=os.getenv("REDIS_HOST", "redis"),
            port=int(os.getenv("REDIS_PORT", "6379")),
        )

        self._pubsub = self._redis.pubsub()

    def listen(self) -> AsyncGenerator:
        return self._pubsub.listen()

    def get_messages(self):
        return self._pubsub.get_message()

    async def subscribe(self, channel: str):
        # pyrefly: ignore [not-async] - in prod, it complains it wasn't awaited
        await self._pubsub.subscribe(channel)

        async def unsubscribe():
            await self._pubsub.unsubscribe(channel)

        return unsubscribe

    async def publish(self, channel: str, message: EncodableT):
        return await self._redis.publish(channel, message)

    async def close(self):
        self._pubsub.close()
        await self._redis.close()


async def get_listener_service():
    service = ListenerService()
    yield service
