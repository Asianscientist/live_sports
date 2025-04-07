from fastapi import WebSocket, WebSocketDisconnect
from app.core.connection_manager import GoalAlertManager
from app.users import auth_user

manager = GoalAlertManager()

async def websocket_updates(websocket: WebSocket, token: str):
    # Authenticate the user
    user = await auth_user.get_current_user(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket, user)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)