# pylint: disable=import-error, too-few-public-methods

"""This module contains common dependencies of fastAPI app"""

from app.database import CollectionHandler


class CollectionDocsViewer:
    """This class contains params and method needed to get documents from
    mongodb collection for api view"""
    def __init__(self, collections: list, db_name: str):
        """Instanciate class with passed collections list and db_name"""
        self.db_collections = collections
        self.db_name = db_name

    def __call__(self,
                 collection_name: str,
                 page_num: int = 1,
                 goods_per_page: int = 100):
        """Returns list of collection documents paginated with passed parameters"""
        if collection_name not in self.db_collections:
            return [{"Collection not found Error": "Collection not found 404"}]
        collection = CollectionHandler(self.db_name, collection_name)
        docs = collection.find(filter={},
                               projection={'id': False},
                               skip=((page_num - 1) * goods_per_page),
                               limit=goods_per_page)
        docs_data = []
        for doc in docs:
            doc['_id'] = str(doc['_id'])
            docs_data.append(doc)
        return docs_data
