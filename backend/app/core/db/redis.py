import redis.asyncio as redis
from fastapi import Depends
from app.core.config.settings import settings


async def get_redis_connection():
    """
    Get a Redis connection from the pool.
    """
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        encoding="utf-8",
        decode_responses=True
    )
    try:
        yield redis_client
    finally:
        await redis_client.close()