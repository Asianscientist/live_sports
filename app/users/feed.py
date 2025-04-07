import asyncio
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
import json
from typing import List
from .auth_user import get_current_user
from tasks import sport_api
from database.redis import get_redis
from datetime import datetime

router = APIRouter(prefix="/users", tags=["auth"])

client=AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
database=client[settings.MONGODB_DATABASE]
user_preference_collection=database['user_preferences']

redis_client=get_redis()

class UserPreferences(BaseModel):
    user_id:str
    favorite_leagues:list[int]
    favorite_teams:list[int]=[]

# @router.get('/interested_parties/{team_id}')
async def give_all_interested_users(team_id):
    try:
        team_id=int(team_id)
        if team_id<=0:
            raise ValueError('Team id  must be a positive number')
        users = await user_preference_collection.find({"favorite_teams": team_id}, {'user_id':1, "_id":0}).to_list()
        interested_users=[user['user_id'] for user in users]
        return interested_users
    
    except Exception as e:
        raise BaseException("Failed")


@router.get("/get-leagues")
async def get_top_leagues(curr_user:str=Depends(get_current_user)):
    user_id=curr_user.id
    data = await sport_api.list_leagues()
    favorite_leagues=[]
    try:
        user_prefs = await user_preference_collection.find_one({"user_id":user_id})
        favorite_leagues=user_prefs.get("favorite_leagues", [])
        for key, val in data.items():
            if val not in favorite_leagues:
                del data[key]
    except Exception as e:
        pass
    return {"popular_leagues":data, "favorite_leagues":favorite_leagues}

@router.get('/get-teams')
async def get_top_teams(current_user:str=Depends(get_current_user)):
    user_id=current_user.id
    prefs = await user_preference_collection.find_one({'user_id':user_id})
    if not prefs:
        raise HTTPException(
            status_code=404,
            detail="No preferences found for this user"
        )
    favorite_leagues=prefs.get("favorite_leagues", [])
    teams=await sport_api.get_top_teams(favorite_leagues)

    favorite_teams=prefs.get('favorite_teams', [])
    # if user_teams:
    #     for id in list(teams.keys()):
    #         if id not in user_teams:
    #             del teams[id]
    return {
        "user_id": current_user.id,
        "top_teams": teams,
        'favorite_teams':favorite_teams
    } 

@router.post('/submit-teams')
async def submit_favorite_teams(team_ids:List[int], curr_user:str=Depends(get_current_user)):
    user_id = curr_user.id
    result=await user_preference_collection.update_one(
            {'user_id':user_id},
            {
                "$set":{
                    "favorite_teams": team_ids,
                }
            }
        )
    updated_prefs = await user_preference_collection.find_one({"user_id": user_id})
    await redis_client.hset(f"user:{user_id}", "favorite_teams", json.dumps(team_ids))
    
    return {
            "message": "Leagues successfully stored",
            "user_id": user_id,
            "stored_teams": updated_prefs["favorite_teams"]
        }

# storing favorite leagues
@router.post("/submit-leagues")
async def submit_favorite_leagues(league_ids:List[int], current_user:str=Depends(get_current_user)):
    user_id = current_user.id
    try:
        result=await user_preference_collection.update_one(
            {'user_id':user_id},
            {
                "$set": {
                    "favorite_leagues": league_ids,
                }
            }
        )
        if result.matched_count==0:
            new_prefs=UserPreferences(
                user_id=user_id, favorite_leagues=league_ids, favorite_teams=[]
            )
        await user_preference_collection.insert_one(new_prefs.dict())

        updated_prefs = await user_preference_collection.find_one({"user_id": user_id})
        await redis_client.hset(f"user:{user_id}", "favorite_leagues", json.dumps(league_ids))
        # cached_data=await redis_client.hget(f"user:{user_id}", "favorite_leagues")
        # print(cached_data, 'cached_data')

        return {
            "message": "Leagues successfully stored",
            "user_id": user_id,
            "stored_leagues": updated_prefs["favorite_leagues"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store leagues {str(e)}")

@router.get("/test12")
async def testirovchik(curr_user:str=Depends(get_current_user)):
    usr_id=curr_user.id
    try:
        cached_data=await redis_client.hget(f"user:{usr_id}", "favorite_leagues")
        cached_data=json.loads(cached_data)
        live_matches=await sport_api.get_current_matches(cached_data, usr_id)
        return live_matches
    
    except Exception as e:
        raise HTTPException(status_code=404, detail="No preferences found for this user")

@router.get("/user-preferences/{user_id}")
async def get_user_preferences(user_id:str):
    user=user_preference_collection.find_one({"user_id":user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop("_id", None)
    return user

@router.get("/last-weeks")
async def get_last_weekdata(curr_user=Depends(get_current_user)):
    user_id=curr_user.id
    favorite_teams=await redis_client.hget(f"user:{user_id}", 'favorite_teams')
    print(favorite_teams)

    return favorite_teams
    # data = await sport_api.get_team_statistics(39, '2024', 33)    
    # return data

