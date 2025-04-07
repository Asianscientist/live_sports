from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

class Settings:
    # MongoDB configurations
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DATABASE = os.getenv("MONGODB_DATABASE", "soccerboard")

    # Redis configurations
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)  # Optional password
    REDIS_DB = int(os.getenv("REDIS_DB", 0))  # Optional DB index

    SECRET_KEY=os.getenv('SECRET_KEY')
    ALGORITHM=os.getenv('ALGORITHM')
settings = Settings()