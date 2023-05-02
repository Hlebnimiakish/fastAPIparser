# pylint: skip-file
# pylint: disable=import-error, too-few-public-methods

"""This module contains common dependencies of fastAPI app"""

from fastapi import BackgroundTasks, HTTPException, Request

from app.database import CollectionHandler
from app.redis_cache import CacheFactory


class CollectionDocsViewer:
    """This class contains params and method needed to get documents from
    mongodb collection for api view"""
    def __init__(self, db_name: str):
        """Instanciate class with passed collections list and db_name"""
        self.db_name = db_name

    def __call__(self,
                 request: Request,
                 background_tasks: BackgroundTasks,
                 collection_name: str,
                 page_num: int = 1,
                 goods_per_page: int = 100):
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
        """Returns list of collection documents from database paginated
        with passed parameters"""
        collection = CollectionHandler(self.db_name, collection_name)
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
    def __init__(self, db_name: str):
        self.db_name = db_name

    def __call__(self,
                 request: Request,
                 background_tasks: BackgroundTasks):
        cache = CacheFactory(self.lamoda_categories_map_getter,
                             expiration=500)
        categories_map = cache.cache_checker(request=request,
                                             background_tasks=background_tasks)
        return categories_map

    def lamoda_categories_map_getter(self):
        collection = CollectionHandler(self.db_name, "categories")
        categories_data = [category for category in collection.find({})]
        if not categories_data:
            raise HTTPException(status_code=404, detail="No categories found")
        categories_map = {}
        for category in categories_data:
            categories_map[category['category_type']] = \
                [key for key in category['subcategories'].keys()]
        return categories_map
