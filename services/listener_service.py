from redis import Redis
from redis.client import PubSub


class ListenerService:
    redis = Redis(host="redis", port=6379)
    pubsub: PubSub = redis.pubsub()
