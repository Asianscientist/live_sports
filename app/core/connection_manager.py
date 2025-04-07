from fastapi import WebSocket
from typing import Dict, List
# from app.schemas.user import UserResponse
from database.redis import get_redis
import asyncio
import json

class GoalAlertManager:
    def __init__(self):
        self.active_connections: Dict[WebSocket, str] = {}
        self.user_websockets={}
        self.redis_client=get_redis()

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[websocket] = user_id
        self.user_websockets[user_id]=websocket

    def disconnect(self, websocket: WebSocket):
        user_id=self.active_connections.pop(websocket, None)
        if user_id:
            self.user_websockets.pop(user_id, None)

    async def subscribe_to_match(self, user_id:str, match_id:int):
        pubsub=self.redis_client.pubsub()
        await pubsub.subscribe(f"match:{match_id}:goals")
        asyncio.create_task(self.listen_for_goals(pubsub, user_id))

    async def listen_for_goals(self, pubsub, user_id):
        async with pubsub:
            while user_id in self.user_websockets:
                try:
                    message=await pubsub.get_message(ignore_subscribe_message=True)
                    if message:
                        goal_data=json.loads(message['data'])
                        await self.send_alerts(user_id, goal_data)
                except Exception as e:
                    print(f"Alert error: {e}")
                    await asyncio.sleep(5)
    
    async def send_alerts(self, user_id, goal_data):
        websocket=self.user_websockets.get(user_id)
        if websocket:
            await websocket.send_text(
                f"GOAL! {goal_data['scorer']} ({goal_data['minute']}')"
            )
