# pylint: skip-file

"""This module contains mongo db client and dbs parameters"""

from typing import Any, Mapping, TypeVar

from pymongo import MongoClient, cursor
from pymongo.results import (DeleteResult, InsertManyResult, InsertOneResult,
                             UpdateResult)

from app.settings import settings

_DocumentType = TypeVar("_DocumentType", bound=Mapping[str, Any])


class DatabaseGetter:
    """Class that contains database created or gotten by passed in name"""
    db_client: MongoClient = MongoClient(settings.mongo_uri)

    def __init__(self, db_name: str) -> None:
        """Instanciate a Database Getter class with given database parameter"""
        self.db = self.db_client.get_database(str(db_name))


class DatabaseCollectionsList(DatabaseGetter):
    """On call returns list of all collections of class instance database"""
    def __call__(self) -> list:
        return self.db.list_collection_names()


class CollectionHandler:
    """Class containing methods for mongo db collection operations handling;
    P.S. 'doc' same as 'document'"""
    def __init__(self, db_name: str, collection_name: str) -> None:
        """Instanciate a Collection Handler class with given database and
        collection parameters"""
        self.db = DatabaseGetter(db_name).db
        self.collection = self.db.get_collection(str(collection_name))

    def find(self, *args, **kwargs) -> cursor.Cursor[_DocumentType]:
        """Duplicates pymongo Collection find method: takes parameters and
        returns cursor (db query) for docs, found with given parameters"""
        docs = self.collection.find(*args, **kwargs)
        return docs

    def find_one(self, *args, **kwargs) -> dict | None:
        """Duplicates pymongo Collection find one method: takes parameters and
        returns the first doc found with given parameters or None if no
        docs were found"""
        doc = self.collection.find_one(*args, **kwargs)
        return doc

    def insert_one(self, *args, **kwargs) -> InsertOneResult:
        """Duplicates pymongo Collection insert one method: takes parameters and
        doc data and inserts it to class' collection, returns InsertOneResult
        from pymongo results"""
        result = self.collection.insert_one(*args, **kwargs)
        return result

    def insert_many(self, *args, **kwargs) -> InsertManyResult:
        """Duplicates pymongo Collection insert one method: takes parameters and
        list of docs' data and inserts them to class' collection, returns
        InsertManyResult from pymongo results"""
        result = self.collection.insert_many(*args, **kwargs)
        return result

    def update_one(self, *args, **kwargs) -> UpdateResult:
        """Duplicates pymongo Collection update one method: takes parameters and
        doc data to be updated (changed) and changes doc data (with passed doc data)
        of first doc found with given parameters, returns UpdateResult
        from pymongo results"""
        result = self.collection.update_one(*args, **kwargs)
        return result

    def update_many(self, *args, **kwargs) -> UpdateResult:
        """Duplicates pymongo Collection update many method: takes parameters and
        doc data to be updated (changed) and changes doc data (with passed doc data)
        of all docs found with given parameters, returns UpdateResult
        from pymongo results"""
        result = self.collection.update_many(*args, **kwargs)
        return result

    def delete_many(self, *args, **kwargs) -> DeleteResult:
        """Duplicates pymongo Collection delete many method: takes parameters
        and deletes all docs found with given parameters, returns DeleteResult
        from pymongo results"""
        result = self.collection.delete_many(*args, **kwargs)
        return result

    def delete_one(self, *args, **kwargs) -> DeleteResult:
        """Duplicates pymongo Collection delete one method: takes parameters
        and deletes the first doc found with given parameters, returns DeleteResult
        from pymongo results"""
        result = self.collection.delete_one(*args, **kwargs)
        return result
