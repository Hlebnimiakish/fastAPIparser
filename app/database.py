# pylint: skip-file

"""This module contains mongo db client and dbs parameters"""

from pymongo import MongoClient

from app.settings import get_settings

db_client: MongoClient = MongoClient(get_settings().mongo_uri)


class DatabaseGetter:
    """Class that contains database created or gotten by passed in name"""
    def __init__(self, db_name: str) -> None:
        """Instanciate a Database Getter class with given database parameter"""
        self.db = db_client.get_database(str(db_name))


class CollectionHandler:
    """Class containing methods for mongo db collection operations handling;
    P.S. 'doc' same as 'document'"""
    def __init__(self, db_name: str, collection_name: str) -> None:
        """Instanciate a Collection Handler class with given database and
        collection parameters"""
        self.db = DatabaseGetter(db_name).db
        self.collection = self.db.get_collection(str(collection_name))

    def get_all_collection_docs_data(self) -> list:
        """Gets and returns all docs data from class collection"""
        docs = self.collection.find()
        docs_data = [doc for doc in docs]
        return docs_data

    def get_doc_by_parameters(self, params: dict) -> dict | None:
        """Gets and returns specific doc found by a given parameters"""
        doc = self.collection.find_one(params)
        return doc

    def get_doc_by_key_value(self, key: str) -> dict | None:
        """Gets and returns specific doc which contains a key with
        given name"""
        doc = self.collection.find_one({}, {str(key): 1})
        if doc:
            doc_id = doc['_id']
            doc = self.collection.find_one({"_id": doc_id})
        return doc

    def add_one_doc(self, document: dict):
        """Adds passed doc to class' collection"""
        self.collection.insert_one(document)

    def add_many_docs(self, documents: list[dict]):
        """Adds all passed docs to class' collection"""
        self.collection.insert_many(documents)

    def change_doc(self, search_params: dict, change_fields: dict):
        """Changes found with given parameters doc with passed data"""
        self.collection.update_one(search_params, change_fields)

    def change_many_docs(self, search_params: dict, change_fields: dict):
        """Changes all found with given parameters docs with passed data"""
        self.collection.update_many(search_params, change_fields)

    def clear_collection(self):
        """Deletes all docs from class' collection"""
        self.collection.delete_many({})

    def delete_doc_by_parameters(self, params: dict):
        """Deletes specific doc from class' collection found with
        given parameters"""
        self.collection.delete_one(params)
