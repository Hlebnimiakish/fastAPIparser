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
    id: ObjectId = Field(default_factory=PyObjectId, alias='_id')
    category_type: str
    subcategories: dict[str, Union[str, list]]
    creation_time: datetime.datetime = Field(default=datetime.datetime.now())

    @classmethod
    def category_data_creator(cls,
                              category_type,
                              subcategories):
        """Creates Category model instance and returns it's vars
        data for mongo db document insert"""
        category = CategoryModel()
        category.category_type = category_type
        category.subcategories = subcategories
        return vars(category)


class GoodModel(BaseObjectIdConfig):
    id: ObjectId = Field(default_factory=PyObjectId, alias='_id')
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
        good = GoodModel()
        good.good_title = title
        good.good_attributes = attributes
        good.good_brand = brand
        good.good_price = price
        return vars(good)
