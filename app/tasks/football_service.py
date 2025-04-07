# from app.core.mongodb import user_preference_collection
from . import sport_api
from database.redis import get_redis
from core.connection_manager import GoalAlertManager
from users.auth_user import get_current_user
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
import asyncio
import json
from typing import List

redis_client=get_redis()
connection_manager = GoalAlertManager()
router = APIRouter(prefix="", tags=["fixtures"])

@router.get('/live-matches')
async def get_live_matches(curr_user:str=Depends(get_current_user)):
    user_id=curr_user.id
    favorite_leagues=await redis_client.hget(f"user:{user_id}", "favorite_leagues")
    matches=await sport_api.get_live_matches(favorite_leagues)
    return matches

@router.get('/upcoming-matches')
async def get_upcoming_matches(curr_user:str=Depends(get_current_user)):
    usr_id=curr_user.id
    favorite_leagues=json.loads(await redis_client.hget(f"user:{usr_id}", "favorite_leagues"))
    result = []
    for league_id in favorite_leagues:
        matches = await sport_api.get_upcoming_matches(league_id)
        result.extend(matches)
    return result

@router.post('/subscribe-matches')
async def subscribe_matches(fixture_ids:List[int], curr_user=Depends(get_current_user)):
    user_id=curr_user.id
    await redis_client.hset(f"user:{user_id}", "subscribed_matches", json.dumps(fixture_ids))
    matches=json.loads(await redis_client.hget(f"user:{user_id}", "subscribed_matches"))
    return f"You subscribed to these matches {matches}"

async def send_goal_alerts(match_id:int, subscribers:list):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"match: {match_id}:goals")
    async with pubsub as listener:
        while True:
            try:
                message=await listener.get_message(ignore_subscribe_message=True)
                if message:
                    goal_data=json.loads(message['data'])
                    for user_id in subscribers:
                        if user_id in connection_manager.active_connections:
                            await connection_manager.active_connections[user_id].send_personal_message(
                                f"GOAL! {goal_data['scorer']} ({goal_data['minute']}')"
                            )
                
            except Exception as e:
                print(f"Error: {e}")
                await asyncio.sleep(5)

                