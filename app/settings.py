# pylint: skip-file

"""This module contains pandantic BaseSettings class with it's config"""

from pydantic import BaseSettings

mongo_uri = "mongodb://localhost:27017"


class Settings(BaseSettings):
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
