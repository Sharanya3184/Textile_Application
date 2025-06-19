import os
from pymongo import MongoClient


MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME", "Textile")


client = MongoClient(MONGO_URL)
db = client[DB_NAME]
users_collection = db['users']
products_collection = db['products']
categories_collection = db['categories']



try:
    users_collection         =  db['users']
    products_collection      =  db['products']
    categories_collection    =  db['categories']
    wishcart_collection      =  db['wishcart']
    print("MongoDB connected successfully")
except Exception as e:
    print(f"MongoDB connection error: {e}")

