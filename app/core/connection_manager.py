from fastapi import WebSocket
from typing import Dict, List
# from app.schemas.user import UserResponse
from database.redis import get_redis
import asyncio
import json
redis_client=get_redis()

class GoalAlertManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, str] = {}
        self.user_websockets={}
        self.redis_client=get_redis()

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[websocket] = user_id
        await redis_client.sadd('active_users', user_id)
        self.user_websockets[user_id]=websocket

    async def disconnect(self, websocket: WebSocket):
        user_id=self.active_connections.pop(websocket, None)
        if user_id:
            await redis_client.srem("active_users", user_id)  
            self.user_websockets.pop(user_id, None)

    async def subscribe_to_match(self, user_id:str, match_id:int):
        pubsub=self.redis_client.pubsub()
        channel_name=f"match:{match_id}:goals"
        await pubsub.subscribe(channel_name)
        asyncio.create_task(self.listen_for_goals(pubsub, user_id, match_id))

    async def listen_for_goals(self, pubsub, user_id, match_id):
        async with pubsub:
            try:
                async for message in pubsub.listen():
                    if message['type']=='message':
                        goal_data=json.loads(message['data'].decode('utf-8'))
                        await self.send_alerts(user_id, goal_data)
            except Exception as e:
                print(f"Alert error: {e}")
                await asyncio.sleep(5)

    async def send_alerts(self, user_id, goal_data):
        websocket=self.user_websockets.get(user_id)
        if websocket:
            notification = (
            "⚽ GOAL! ⚽\n"
            f"🏆 {goal_data['team']}\n"
            f"👟 Scorer: {goal_data['scorer']}\n"
            f"🎯 Assist: {goal_data['assist']}\n"
            f"⏱ Minute: {goal_data['minute']}'\n"
            f"📊 Score: {goal_data['score']}"
        )
            await websocket.send_text(notification)
