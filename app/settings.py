# pylint: skip-file

"""This module contains pandantic BaseSettings class with it's config"""

from pydantic import BaseSettings


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://mongodb:27017"
    lamoda_db_name: str = "lamodadb"

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
