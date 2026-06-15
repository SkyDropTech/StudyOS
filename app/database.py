# app/database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Connect to MongoDB
MONGO_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)

# Define Database and Collection
db = client.StudyOS_DB
notebook_collection = db.Notebook_code

print("✅ Successfully connected to StudyOS_DB -> Notebook_code")