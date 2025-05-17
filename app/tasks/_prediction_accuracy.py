from motor.motor_asyncio import AsyncIOMotorClient
from core.config import settings
from database.redis import get_redis

client=AsyncIOMotorClient(settings.MONGODB_URL, serverSelectionTimeoutMS=5000)
database=client[settings.MONGODB_DATABASE]
score_prediction_collection=database['score_predictions']
users_collection=database['users']

redis_client=get_redis()


async def compute_predictions(match, match_id):
    final_home=match['goals']['home']
    final_away=match['goals']['away']

    predictions=predictions.find({'match_id':match_id})
    async for p in predictions:
        predicted_home=p['predicted_home_score']
        predicted_away=p['predicted_away_score']

        if predicted_home==final_home and predicted_away==final_away:
            points=5
        elif ((predicted_home > predicted_away and final_home > final_away) or
              (predicted_home < predicted_away and final_home < final_away) or
              (predicted_home == predicted_away and final_home == final_away)):
            points = 3
        else:
            points=0

        await predictions.update_one(
            {"_id": p['_id']},
            {"$set": {"points_awarded": points}}
        )
        await users_collection.update_one(
            {"_id": p['user_id']},
            {"$inc": {"total_score": points}}
        )
