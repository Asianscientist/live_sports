import requests
from datetime import datetime, timedelta
import httpx
today=datetime.today()
from database.redis import get_redis
import json

redis_client=get_redis()
url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

headers = {
	"x-rapidapi-key": "ddc3664991msh704bd9ad75426cep1496f9jsnb8ad8b1e6a82",
	"x-rapidapi-host": "api-football-v1.p.rapidapi.com"
}

def get_fixtures_byleague_season(league, season='2024'):
    querystring = {"league":league, "season":season}
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code == 200:
        data = response.json()
        fixtures = data.get("response", [])
        
        # Filter fixtures up to today
        filtered_fixtures = []
        for fixture in fixtures:
            fixture_date_str = fixture["fixture"]["date"]
            fixture_date = datetime.strptime(fixture_date_str, "%Y-%m-%dT%H:%M:%S%z")  # Parse fixture date
            if fixture_date.date() <= today.date():  # Compare dates
                filtered_fixtures.append(fixture)
        
        if filtered_fixtures:
            return filtered_fixtures
        else:
            print(f"No fixtures found up to today ({today.strftime('%Y-%m-%d')}).")

# print(get_fixtures_byleague_season("39","2024"))

async def get_current_matches(leagues, user_id):
    querystring = {"live":"all"}    

    async with httpx.AsyncClient() as client:
        response = requests.get(url, headers=headers, params=querystring)
    data = response.json().get('response', [])
    
    collection=[]
    live_fixture_ids=[]
    for x in data:
        if x['league']['id'] in leagues:
            live_fixture_ids.append(x['fixture']['id'])
            collection.append(x)
    await redis_client.hset(f"user:{user_id}", "live_fixture_ids", json.dumps(live_fixture_ids))
    return collection

async def get_upcoming_matches(league_id, user_id=None):
    today = datetime.now().strftime("%Y-%m-%d")  
    next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")  # "2025-04-07"
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"

    querystring = {
        "league": league_id,  # Filter by league
        "season": 2024,     # Filter by season
        "from": today,        # Start date (today)
        "to": next_week,      # End date (7 days from now)
        "status": "NS"        # Only upcoming matches (Not Started)
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, params=querystring)
            response.raise_for_status()
            data = response.json().get('response', [])
            
            matches = []
            for fixture_data in data:
                match = {
                    "fixture": {
                        "id": fixture_data["fixture"]["id"],
                        "date": fixture_data["fixture"]["date"],
                        "status": fixture_data["fixture"]["status"],
                    },
                    "teams": fixture_data["teams"]
                }
                matches.append(match)
            return matches
        
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
            return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return []


async def list_leagues():
    url = "https://api-football-v1.p.rapidapi.com/v3/leagues"
    cached_data=await redis_client.get("popular_league_ids")
    if cached_data:
        return eval(cached_data.decode())
    
    async with httpx.AsyncClient() as client:
        response = requests.get(url, headers=headers)
    data = response.json().get('response', [])
    
    popular_leagues = [
        "Premier League", "La Liga", "Bundesliga", "Serie A", "Ligue 1",
        "UEFA Champions League", "UEFA Europa League", "FA Cup", "Copa del Rey", "MLS"
    ]
    league_ids={}
    for league in data:
        if league['league']['name'] in popular_leagues and league['league']['name'] not in league_ids:
            league_ids[league['league']['name']]=league['league']['id']
    await redis_client.set("popular_league_ids", str(league_ids), ex=86400)
    return league_ids

async def get_top_teams(league_ids):
    popular_teams={}
    async with httpx.AsyncClient() as client:
        for league_id in league_ids:
            url = "https://api-football-v1.p.rapidapi.com/v3/teams"
            query={"league":league_id, 'season':'2024'}
            response=await client.get(url, headers=headers, params=query)
            data=response.json().get('response', [])
            # redis_client.zadd("popular_teams", {data['team']['id']:data['team']['name']})
            # for x in data:
            #     await redis_client.zadd("favorite_teams", {x['team']['id']:x['team']['name']})
            for team in data:
                popular_teams[team['team']['id']]=team['team']['name']
    return popular_teams

def get_fixtures_by_team(team, season='2024'):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    querystring={'season':season, 'team':team}
    response = requests.get(url, headers=headers, params=querystring)
    return response.json().get('response')

async def get_team_statistics(league=39, season='2024', team=None):
    url = "https://api-football-v1.p.rapidapi.com/v3/teams/statistics"
    querystring = {"league":league,"season":season,"team":team}
    async with httpx.AsyncClient() as client:
        response = requests.get(url, headers=headers, params=querystring)
    return response.json().get('response')

async def get_user_relevant_live_matches(user_id):
    subs_ids = await redis_client.hget(f"user:{user_id}", "subscribed_matches")
    fav_leagues=await redis_client.hget(f"user:{user_id}", "favorite_leagues")
    if not fav_leagues or not subs_ids:
        return []
    fav_leagues=json.loads(fav_leagues)
    subs_ids=json.loads(subs_ids)
    live_matches = await get_current_matches(fav_leagues, user_id)
    if not live_matches:
        return []
    relevant_matches = [
        match for match in live_matches if int(match['fixture']['id']) in subs_ids
    ]
    return relevant_matches



async def fetch_football_data():
    pass

