import requests
import asyncio
import json
from datetime import datetime
from database.redis import get_redis
import httpx
from . import sport_api
from core.connection_manager import GoalAlertManager

redis_client=get_redis()
match_goals_cache = {}  #  goal_count

manager=GoalAlertManager()

async def get_live_match_details(match_id):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/events"
    params = {"fixture": match_id}
    headers = {
        "x-rapidapi-key": "ddc3664991msh704bd9ad75426cep1496f9jsnb8ad8b1e6a82",
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json().get("response", [])
        return []


async def poll_live_matches():
    while True:
        try:
            current_users=await redis_client.smembers('active_users')
            users = [u.decode('utf-8') for u in current_users]
            for user_id in users:
                relevant_live_matches=await sport_api.get_user_relevant_live_matches(user_id)
                for match in relevant_live_matches:
                    fixture=match['fixture']
                    match_id=fixture['id']
                    
                    if match_id not in match_goals_cache:
                        match_goals_cache[match_id] = {
                            "count": 0,
                            "last_events": [],
                            "last_check": datetime.now().isoformat()
                        }
                    events=await get_live_match_details(match_id)
                    goal_events=[
                        e for e in events 
                        if e.get("type") == "Goal" 
                        and e["time"]["elapsed"] > match_goals_cache[match_id].get("last_elapsed", 0)
                    ]
                    for event in goal_events:
                        goal_data = {
                            "match_id": match_id,
                            "scorer": event["player"]["name"],
                            "team": event["team"]["name"],
                            "minute": event["time"]["elapsed"],
                            "timestamp": datetime.now().isoformat(),
                            "assist": event.get("assist", {}).get("name", "None"),
                            "score": f"{match['goals']['home']}-{match['goals']['away']}"
                        }

                        await redis_client.publish(
                            f"match:{match_id}:goals",
                            json.dumps(goal_data)
                        )
                        match_goals_cache[match_id]={
                            "count": match_goals_cache[match_id]["count"] + 1,
                            "last_events": match_goals_cache[match_id]["last_events"] + [goal_data],
                            "last_check": datetime.now().isoformat(),
                            "last_elapsed": event["time"]["elapsed"]
                        }
                        if fixture['status']['short']=='FT':
                           # match is over, compute prediction accuracy
                           # final_data = match_goals_cache[match_id]
                            # await store_match_final_data(match_id, final_data)  # Your DB storage function
                            del match_goals_cache[match_id]  
                            await redis_client.delete(f"match:{match_id}:goals")  
                            
                            #remove id from redis cache
                            key_pair=f"user:{user_id}"
                            user_subscribes=json.loads(await redis_client.hget(key_pair, "subscribed_matches"))
                            user_subscribes.remove(match_id)
                            if user_subscribes:
                                await redis_client.hset(key_pair, json.dumps('subscribed_matches'))
                        continue 
        except httpx.HTTPStatusError as e:
            print(f"HTTP error: {e.response.status_code}")
            await asyncio.sleep(60) 
        except Exception as e:
            print(f"Polling error: {e}")
            await asyncio.sleep(30)
        else:
            await asyncio.sleep(15)

