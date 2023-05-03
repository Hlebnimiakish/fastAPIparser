# pylint: skip-file

"""This module contains twitch fastAPI router with it's API requests"""

from typing import Annotated, Union

from fastapi import APIRouter, Depends

from app.database import DatabaseCollectionsList, DatabaseNameGetter
from app.dependencies import CollectionDocsViewer
from app.exceptions import unpredicted_exception_raising
from app.schema import TwitchChannel, TwitchGame, TwitchStream
from app.settings import settings
from kafka_starter.kafka_producer import task_sender_with_check

twitch_db_name = DatabaseNameGetter(settings.TWITCH_DB_NAME)

twitch_db_collections = DatabaseCollectionsList(twitch_db_name())

twitch_router = APIRouter(prefix='/twitch',
                          tags=['twitch'])

docs_viewer = CollectionDocsViewer(db_name=twitch_db_name())


@twitch_router.post("/parse_all_data",
                    response_model=dict[str, str],
                    summary="Send task for database update with actual information about"
                            "top games, their streams and streamer channels",
                    response_description="Task status")
async def parse_twitch_data():
    return unpredicted_exception_raising(
        task_sender_with_check("twitch_data_parser", b'Twitch data renewal task')
    )


@twitch_router.get("/available_collections",
                   response_model=list[str],
                   summary="Returns all available database collections list",
                   response_description="Collections list")
async def get_twitch_collections_list(collections:
                                      Annotated[list, Depends(twitch_db_collections)]):
    return unpredicted_exception_raising(collections)


@twitch_router.get("/view_collection_data",
                   response_model=list[Union[TwitchStream,
                                             TwitchChannel,
                                             TwitchGame,
                                             dict[str, str]]],
                   summary="Returns list of collection documents paginated with passed parameters",
                   response_description="Collections documents list")
async def view_collection_data(docs: Annotated[list, Depends(docs_viewer)]):
    return unpredicted_exception_raising(docs)
