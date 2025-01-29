# database.py
from pymongo import MongoClient
import gridfs
import config

client = MongoClient(config.MONGO_URI)
db = client["data_analysis"]
fs = gridfs.GridFS(db)