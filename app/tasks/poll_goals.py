import requests
import asyncio
import json
from datetime import datetime
from database.redis import get_redis

redis_client=get_redis()

async def poll_live_matches():
    headers = {
        "x-rapidapi-key": "ddc3664991msh704bd9ad75426cep1496f9jsnb8ad8b1e6a82",
        "x-rapidapi-host": "api-football-v1.p.rapidapi.com"
    }
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    params={'live':'all'}
    while True:
        response=requests.get(url, headers, params)
        if response.status_code==200:
            matches=response.json()['response']
            for match in matches:
                match_id=match['fixture']['id']


