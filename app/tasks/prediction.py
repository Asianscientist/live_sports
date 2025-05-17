import asyncio
from fastapi import Depends, FastAPI, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
import json
import requests
from typing import List
from users.auth_user import get_current_user
from tasks import sport_api
from database.redis import get_redis
from datetime import datetime

router = APIRouter(prefix="/predictions")

client=AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
database=client[settings.MONGODB_DATABASE]
score_prediction_collection=database['score_predictions']

redis_client=get_redis()

headers = {
	"x-rapidapi-key": "ddc3664991msh704bd9ad75426cep1496f9jsnb8ad8b1e6a82",
	"x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

class PredictionModel(BaseModel):
    user_id:str
    match_id:str
    predicted_home_score:int
    predicted_away_score:int
    points_awarded:int=0
    submitted_at: datetime = datetime.now()
    


@router.post("/matches/{match_id}/predict")
async def create_prediction(match_id, home_score, away_score, curr_user=Depends(get_current_user)):
    user_id=curr_user.id
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring = {"id":match_id}
    response = requests.get(url, headers=headers, params=querystring).json()
    status = response['response'][0]['fixture']['status']['short']
    if status!='NS':
        raise HTTPException(400, "Match is not available for predictions")
    existing_prediction = await score_prediction_collection.find_one({
        "user_id": user_id,
        "match_id": match_id
    })
    prediction_data = {
        "user_id": user_id,
        "match_id": match_id,
        "predicted_home_score": home_score,
        "predicted_away_score": away_score,
        "submitted_at": datetime.now()
    }
    if existing_prediction:
        await score_prediction_collection.update_one(
        {"_id": existing_prediction['_id']},  
        {'$set': prediction_data}
    )
    else:
        await score_prediction_collection.insert_one(prediction_data)
    await redis_client.publish(
        f"predictions:{match_id}",
        f"New prediction by {curr_user.username}"
    )
    return {'message':'Prediction saved successfully'}



