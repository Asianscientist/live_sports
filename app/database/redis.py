import redis.asyncio as redis  # Async Redis client
from core.config import settings

# Redis connection
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,  # Optional password
    db=settings.REDIS_DB  # Optional DB index
)

def get_redis():
    return redis_client