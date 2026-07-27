from enum import StrEnum
from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from redis.client import PubSub
from redis.typing import EncodableT


class Channels(StrEnum):
    EXPORTS = "exports"


class ListenerService:
    redis = Redis(host="redis", port=6379)
    pubsub: PubSub = redis.pubsub()

    def listen(self) -> AsyncGenerator:
        return self.pubsub.listen()

    def get_messages(self):
        return self.pubsub.get_message()

    def subscribe(self, channel: str):
        return self.pubsub.subscribe(channel)

    async def publish(self, channel: str, message: EncodableT):
        return await self.redis.publish(channel, message)

    async def close(self):
        self.pubsub.close()
        await self.redis.close()


async def get_listener_service():
    service = ListenerService()
    yield service
