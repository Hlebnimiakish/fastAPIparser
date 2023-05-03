# pylint: skip-file

"""This module contains database models for mongo db interaction"""

import datetime
from typing import Union

from bson import ObjectId
from pydantic import BaseModel, Field


class PyObjectId(ObjectId):
    """Converts BSON ObjectId to string and adds validation"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid objectid")
        return ObjectId(value)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class BaseObjectIdConfig(BaseModel):
    """Base class containing config class for mongo db models"""
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class CategoryModel(BaseObjectIdConfig):
    id: str = Field(default_factory=PyObjectId, alias='_id')
    category_type: str
    subcategories: dict[str, Union[str, list]]
    creation_time: datetime.datetime = Field(default=datetime.datetime.now())

    @classmethod
    def category_data_creator(cls,
                              category_type,
                              subcategories):
        """Creates Category model instance and returns it's vars
        data for mongo db document insert"""
        category = CategoryModel(category_type=category_type,
                                 subcategories=subcategories)
        return vars(category)


class GoodModel(BaseObjectIdConfig):
    id: str = Field(default_factory=PyObjectId, alias='_id')
    good_title: str
    good_brand: str
    good_attributes: list[dict]
    good_price: float
    creation_time: datetime.datetime = Field(default=datetime.datetime.now())

    @classmethod
    def good_data_creator(cls,
                          title,
                          brand,
                          attributes,
                          price):
        """Creates Good model instance and returns it's vars
        data for mongo db document insert"""
        good = GoodModel(good_title=title,
                         good_attributes=attributes,
                         good_brand=brand,
                         good_price=price)
        return vars(good)


class ParseCategory(BaseModel):
    category_type: str
    subcategory: str
    pages_to_parse_limiter: int = 3


class ParsePage(BaseModel):
    page_to_parse: str


class TwitchGame(BaseObjectIdConfig):
    id: str = Field(default_factory=PyObjectId, alias='_id')
    game_id: int
    game_name: str
    creation_time: datetime.datetime = Field(default=datetime.datetime.now())

    @classmethod
    def twitch_game_data_creator(cls,
                                 game_id,
                                 game_name):
        game = TwitchGame(game_id=game_id,
                          game_name=game_name)
        return vars(game)


class TwitchStream(BaseObjectIdConfig):
    id: str = Field(default_factory=PyObjectId, alias='_id')
    twitch_id: str
    user_id: str
    user_login: str
    user_name: str
    game_id: str | None
    game_name: str | None
    type: str | None
    title: str | None
    viewer_count: int | None
    started_at: datetime.datetime | None
    language: str | None
    thumbnail_url: str | None
    tag_ids: list[int] | list
    tags: list[str] | list | None
    is_mature: bool | None
    creation_time: datetime.datetime = Field(default=datetime.datetime.now())

    @classmethod
    def twitch_stream_data_creator(cls,
                                   stream_params: dict):
        stream_params['twitch_id'] = stream_params.pop('id')
        stream = TwitchStream(**stream_params)
        return vars(stream)


class TwitchChannel(BaseObjectIdConfig):
    id: str = Field(default_factory=PyObjectId, alias='_id')
    broadcaster_id: str
    broadcaster_login: str
    broadcaster_name: str
    broadcaster_language: str | None
    game_id: str | None
    game_name: str | None
    title: str | None
    delay: int | None
    tags: list[str] | list | None
    creation_time: datetime.datetime = Field(default=datetime.datetime.now())

    @classmethod
    def twitch_channel_data_creation(cls,
                                     channel_params: dict):
        channel = TwitchChannel(**channel_params)
        return vars(channel)
