# pylint: skip-file

"""This module contains twitch fastAPI router with it's API requests"""

from typing import Annotated, Union

from fastapi import APIRouter, Depends

from app.database import DatabaseCollectionsList
from app.dependencies import CollectionDocsViewer
from app.schema import TwitchChannel, TwitchGame, TwitchStream
from app.settings import settings
from kafka_starter.kafka_producer import producer

twitch_db_name = settings.twitch_db_name

twitch_db_collections = DatabaseCollectionsList(twitch_db_name)

twitch_router = APIRouter(prefix='/twitch',
                          tags=['twitch'])

docs_viewer = CollectionDocsViewer(db_name=twitch_db_name,
                                   collections=twitch_db_collections())


@twitch_router.post("/parse_all_data",
                    response_model=dict[str, str],
                    summary="Send task for database update with actual information about"
                            "top games, their streams and streamer channels",
                    response_description="Task status")
async def parse_twitch_data():
    producer.send("twitch_data_parser", b'Twitch data renewal task')
    producer.flush()
    return {"Task send": "Twitch data renewal task send"}


@twitch_router.get("/available_collections",
                   response_model=list[str],
                   summary="Returns all available database collections list",
                   response_description="Collections list")
async def get_twitch_collections_list(collections:
                                      Annotated[list, Depends(twitch_db_collections)]):
    return collections


@twitch_router.get("/view_collection_data",
                   response_model=list[Union[TwitchStream,
                                             TwitchChannel,
                                             TwitchGame,
                                             dict[str, str]]],
                   summary="Returns list of collection documents paginated with passed parameters",
                   response_description="Collections documents list")
async def view_collection_data(docs: Annotated[list, Depends(docs_viewer)]):
    return docs
