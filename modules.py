import os
from pymongo import MongoClient


MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "Textile")
