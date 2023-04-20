# pylint: skip-file

"""This module contains mongo db client and dbs parameters"""

from pymongo import MongoClient

from app.settings import get_settings


class DatabaseGetter:
    """Class that contains database created or gotten by passed in name"""
    db_client: MongoClient = MongoClient(get_settings().mongo_uri)

    def __init__(self, db_name: str) -> None:
        """Instanciate a Database Getter class with given database parameter"""
        self.db = self.db_client.get_database(str(db_name))


class CollectionHandler:
    """Class containing methods for mongo db collection operations handling;
    P.S. 'doc' same as 'document'"""
    def __init__(self, db_name: str, collection_name: str) -> None:
        """Instanciate a Collection Handler class with given database and
        collection parameters"""
        self.db = DatabaseGetter(db_name).db
        self.collection = self.db.get_collection(str(collection_name))

    def get_all_data(self) -> list:
        """Gets and returns all docs data from class collection"""
        docs = self.collection.find()
        docs_data = [doc for doc in docs]
        return docs_data

    def find(self, params: dict) -> list[dict] | None:
        """Gets and returns all docs data with given parameters from
        class collection"""
        docs = self.collection.find(params)
        docs_data = [doc for doc in docs]
        return docs_data

    def find_one_by_params(self, params: dict) -> dict | None:
        """Gets and returns specific doc found by a given parameters"""
        doc = self.collection.find_one(params)
        return doc

    def find_one_by_key(self, key: str) -> dict | None:
        """Gets and returns specific doc which contains a key with
        given name"""
        doc = self.collection.find_one({}, {str(key): 1})
        if doc:
            doc_id = doc['_id']
            doc = self.collection.find_one({"_id": doc_id})
        return doc

    def find_with_pagination(self, cursor: str | None) \
            -> dict[str, list | str | None]:
        if cursor:
            docs = self.collection.find({}, {"_id": {"$gt": cursor}}).sort("_id", -1)
        else:
            docs = self.collection.find({}).sort("_id", -1)
        docs_data = []
        for doc in docs.limit(100):
            docs_data.append(doc)
            cursor = doc["_id"]
        return {"data": docs_data, "cursor": cursor}

    def insert_one(self, document: dict):
        """Adds passed doc to class' collection"""
        self.collection.insert_one(document)

    def insert_many(self, documents: list[dict]):
        """Adds all passed docs to class' collection"""
        self.collection.insert_many(documents)

    def update_one(self, search_params: dict, change_fields: dict):
        """Changes found with given parameters doc with passed data"""
        self.collection.update_one(search_params, change_fields)

    def update_many(self, search_params: dict, change_fields: dict):
        """Changes all found with given parameters docs with passed data"""
        self.collection.update_many(search_params, change_fields)

    def delete_many(self, params: dict):
        """Deletes all docs from class' collection"""
        self.collection.delete_many(params)

    def delete_one(self, params: dict):
        """Deletes specific doc from class' collection found with
        given parameters"""
        self.collection.delete_one(params)
