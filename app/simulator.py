import redis
import json

r = redis.Redis(host="localhost", port=6379, db=0)
goal_data = {
    "scorer": "Jude Bellingham",
    "minute": "24"
}
r.publish("match:1208756:goals", json.dumps(goal_data))