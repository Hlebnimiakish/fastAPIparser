# pylint: skip-file

"""This module contains pandantic BaseSettings class with it's config"""

from functools import lru_cache

from pydantic import BaseSettings


@lru_cache()
def get_settings():
    return Settings()


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://mongodb:27017"
    lamoda_db_name: str = "lamodadb"

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
