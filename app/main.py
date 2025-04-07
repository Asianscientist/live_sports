from fastapi import FastAPI, status
from routes import *
from core.config import settings
from users import auth_user, feed
from tasks import football_service
from core import endpoints
from tasks.sport_api import fetch_football_data

app=FastAPI(title="Real-time chat app", version="1.0.0")

app.include_router(auth_user.router, prefix="/api/v1/uers", tags=['users'])
app.include_router(feed.router, prefix="/api/v1/feed", tags=['user-feed'])
app.include_router(football_service.router, prefix="/api/v1/fixtures", tags=['fixture'])
app.include_router(endpoints.router)

@app.on_event("startup")
async def startup_event():
    import asyncio
    asyncio.create_task(fetch_football_data())

if __name__=='__main__':
    print(app.routes)
    import uvicorn
    uvicorn.run(app,host="0.0.0.0", port=8000)

    
