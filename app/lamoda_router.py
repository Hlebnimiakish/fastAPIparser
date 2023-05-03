# pylint: skip-file

"""This module contains lamoda fastAPI router with it's API requests"""

import json
from typing import Annotated, Union

from fastapi import APIRouter, Depends

from app.database import CollectionHandler, DatabaseCollectionsList
from app.dependencies import CollectionDocsViewer
from app.schema import GoodModel, ParseCategory, ParsePage
from app.settings import settings
from kafka_starter.kafka_producer import producer

lamoda_db_name = settings.lamoda_db_name

lamoda_db_collections = DatabaseCollectionsList(lamoda_db_name)

lamoda_router = APIRouter(prefix='/lamoda',
                          tags=['lamoda'])

docs_viewer = CollectionDocsViewer(db_name=lamoda_db_name,
                                   collections=lamoda_db_collections())


@lamoda_router.post("/category_renewal",
                    response_model=dict[str, str],
                    summary="Update database with current actual category map",
                    response_description="Task status")
async def renew_category_map():
    producer.send("lamoda_category_parser", b"Category map renewal task")
    producer.flush()
    return {"Task send": "Category map renewal task send"}


@lamoda_router.get("/get_category_map",
                   response_model=dict[str, list],
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


@lamoda_router.get("/available_collections",
                   response_model=list[str],
                   summary="Returns all available database collections list",
                   response_description="Collections list")
async def get_lamoda_collections_list(collections:
                                      Annotated[list, Depends(lamoda_db_collections)]):
    return collections


@lamoda_router.put("/parse_category",
                   response_model=dict[str, str],
                   summary="Takes in category_type and subcategory and "
                           "sends parsing task to kafka",
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


@lamoda_router.get("/view_category_goods",
                   response_model=list[Union[GoodModel, dict[str, str]]],
                   summary="Returns list of category goods, paginated with passed parameters",
                   response_description="Category goods list")
async def view_category_goods(docs: Annotated[list, Depends(docs_viewer)]):
    return docs


@lamoda_router.put("/parse_goods_from_page",
                   response_model=dict[str, str],
                   summary="Set task to parse passed page link and adds to database all goods from"
                           "passed page",
                   response_description="Task status or error")
async def parse_passed_page(page_link: ParsePage):
    message = json.dumps(page_link.dict()).encode('utf-8')
    producer.send("lamoda_page_parser", message)
    producer.flush()
    return {"Task send": "Page parsing task send"}
