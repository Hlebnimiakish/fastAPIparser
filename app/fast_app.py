# pylint: skip-file

"""This module contains FastAPI app and it's APIs methods"""

import json

from fastapi import FastAPI

from app.database import CollectionHandler, DatabaseGetter
from app.schema import ParseCategory, ParsePage
from app.settings import settings
from kafka_starter.kafka_producer import producer

fast_app = FastAPI()
lamoda_db_name = settings.lamoda_db_name


@fast_app.post("/category_renewal/",
               summary="Update database with current actual category map",
               response_description="Task status")
async def renew_category_map():
    producer.send("lamoda_category_parser", b"Category map renewal task")
    producer.flush()
    return {"Task send": "Category map renewal task send"}


@fast_app.get("/get_category_map/",
              summary="Returns current actual categories and subcategories",
              response_description="Current actual categories and subcategories")
async def get_category_map():
    collection = CollectionHandler(lamoda_db_name, "categories")
    categories_data = [category for category in collection.find({})]
    categories_map = {}
    for category in categories_data:
        categories_map[category['category_type']] = \
            [key for key in category['subcategories'].keys()]
    return categories_map


@fast_app.get("/available_collections/",
              summary="Returns all available database collections list",
              response_description="Collections list")
async def get_collections_list():
    db = DatabaseGetter(lamoda_db_name).db
    collections = db.list_collection_names()
    return collections


@fast_app.put("/parse_category/",
              summary="Takes in category_type and subcategory and sends parsing task to kafka",
              response_description="Task status or error")
async def parse_category(category_params: ParseCategory):
    collection = CollectionHandler(lamoda_db_name, "categories")
    document = collection.find_one({"category_type":
                                    category_params.category_type})
    if not document:
        return {"Category Error": "Category not found 404"}
    if not document["subcategories"][category_params.subcategory]:
        return {"Subcategory Error": "Subcategory not found 404"}
    message = json.dumps(category_params.dict()).encode('utf-8')
    producer.send("lamoda_goods_parser", message)
    producer.flush()
    return {"Task send": "Category parsing task send"}


@fast_app.get("/view_category_goods/",
              summary="Returns list of 100 category goods from cursor",
              response_description="Up to 100 category goods list")
async def view_category_goods(collection_name: str,
                              page_num: int = 1,
                              goods_per_page: int = 100):
    db = DatabaseGetter(lamoda_db_name).db
    collections = db.list_collection_names()
    if collection_name not in collections:
        return {"Collection not found Error": "Collection not found 404"}
    collection = CollectionHandler(lamoda_db_name, collection_name)
    docs = collection.find(filter={},
                           projection={'id': False},
                           skip=((page_num - 1) * goods_per_page),
                           limit=goods_per_page)
    docs_data = []
    for doc in docs:
        doc['_id'] = str(doc['_id'])
        docs_data.append(doc)
    return docs_data


@fast_app.put("/parse_goods_from_page/",
              summary="Set task to parse passed page link and adds to database all goods from"
                      "passed page",
              response_description="Task status or error")
async def parse_passed_page(page_link: ParsePage):
    message = json.dumps(page_link.dict()).encode('utf-8')
    producer.send("lamoda_page_parser", message)
    producer.flush()
    return {"Task send": "Page parsing task send"}
