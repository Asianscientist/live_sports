from fastapi import WebSocket, WebSocketDisconnect, Depends, APIRouter
from .connection_manager import GoalAlertManager
from users.auth_user import get_current_user
# from .schemas.user import UserResponse
from tasks import sport_api
from users.feed import user_preference_collection
from database.redis import get_redis
redis_client=get_redis()
import json

router = APIRouter(prefix="/ws", tags=["websocket"])
manager=GoalAlertManager()

@router.websocket("/goal-alerts")
async def websocket_endpoint(websocket:WebSocket, token:str):
    user=await get_current_user(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # user_prefs=await 
    # subscribed_matches=sport_api.get_current_matches([])
    subscribed_matches = json.loads(await redis_client.hget(
        {"user_id": user.id},
        {"subscribed_matches": 1}
    ))
    await manager.connect(websocket, user.id)

    for match_id in subscribed_matches:
        await manager.subscribe_to_match(user.id, match_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

        