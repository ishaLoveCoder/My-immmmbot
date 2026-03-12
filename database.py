from motor.motor_asyncio import AsyncIOMotorClient
import os

MONGO_URL = os.getenv("MONGO_URL")
DB_NAME = os.getenv("DB_NAME", "imdbbot")

client = AsyncIOMotorClient(MONGO_URL)

db = client[DB_NAME]

users = db.users
groups = db.groups
templates = db.templates
bans = db.bans
