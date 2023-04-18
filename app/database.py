# pylint: skip-file

"""This module contains mongo db client and dbs parameters"""

from pymongo import MongoClient

from app import settings

db_client: MongoClient = MongoClient(settings.mongo_uri)
lamoda_db = db_client.lamoda_db
