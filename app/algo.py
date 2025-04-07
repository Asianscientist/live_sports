import asyncio
import websockets

async def listen_alerts():
    uri = "ws://localhost:8000/ws/goal-alerts"
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzZXZpbmNoIiwiZXhwIjoxNzQzNTkwMzY0fQ.UBL6gpoKZ-4cgMCwKMxfua39n22YRTVwW5JkPzCXeno"}
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        while True:
            message = await websocket.recv()
            print("GOAL ALERT:", message)

asyncio.get_event_loop().run_until_complete(listen_alerts())

