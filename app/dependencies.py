# pylint: disable=import-error, too-few-public-methods, too-many-arguments

"""This module contains common dependencies of fastAPI app"""

from fastapi import BackgroundTasks, HTTPException, Request

from app.database import CollectionHandler
from app.redis_cache import CacheFactory


class CollectionDocsViewer:
    """This class contains params and method needed to get documents data of
    some mongodb collection (requested from db or from cache) for api view"""
    def __init__(self, db_name: str):
        """Instanciate class with passed collections list and db_name"""
        self.db_name = db_name

    def __call__(self,
                 request: Request,
                 background_tasks: BackgroundTasks,
                 collection_name: str,
                 page_num: int = 1,
                 goods_per_page: int = 100):
        """On call returns docs data from database or cache"""
        cache = CacheFactory(self.docs_getter)
        docs = cache.cache_checker(request=request,
                                   background_tasks=background_tasks,
                                   collection_name=collection_name,
                                   page_num=page_num,
                                   goods_per_page=goods_per_page)
        return docs

    def docs_getter(self,
                    collection_name: str,
                    page_num: int = 1,
                    goods_per_page: int = 100):
        """Returns list of collection documents from database or cache
        paginated with passed parameters"""
        collection = CollectionHandler(self.db_name, collection_name)
        if collection_name == "categories":
            raise HTTPException(status_code=400,
                                detail="This collection can't be parsed")
        docs = collection.find(filter={},
                               projection={'id': False},
                               skip=((page_num - 1) * goods_per_page),
                               limit=goods_per_page)
        docs_data = []
        for doc in docs:
            doc['_id'] = str(doc['_id'])
            docs_data.append(doc)
        if not docs_data:
            raise HTTPException(status_code=404,
                                detail="Collection is empty or doesn't exist")
        return docs_data


class CategoriesMapViewer:
    """This class contains params and method needed to get lamoda categories
    map (requested from db or from cache) for api view"""
    def __init__(self, db_name: str):
        """Instanciate class with passed database name parameter"""
        self.db_name = db_name

    def __call__(self,
                 request: Request,
                 background_tasks: BackgroundTasks):
        """On call returns categories map data from database or cache"""
        cache = CacheFactory(self.lamoda_categories_map_getter,
                             expiration=500)
        categories_map = cache.cache_checker(request=request,
                                             background_tasks=background_tasks)
        return categories_map

    def lamoda_categories_map_getter(self):
        """Returns categories map from database or cache"""
        collection = CollectionHandler(self.db_name, "categories")
        categories_data = list(collection.find({}))
        if not categories_data:
            raise HTTPException(status_code=404, detail="No categories found")
        categories_map = {}
        for category in categories_data:
            categories_map[category['category_type']] = \
                list(category['subcategories'].keys())
        return categories_map
