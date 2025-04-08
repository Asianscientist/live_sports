import json
from database.redis import get_redis
import asyncio

redis_client=get_redis()

async def publish_goal():
    channel="match:1208769:goals"
    goal_data = {
        "scorer": "Ferran Torres",
        "minute": 24
    }
    await redis_client.publish(channel, json.dumps(goal_data))
    
asyncio.run(publish_goal())
