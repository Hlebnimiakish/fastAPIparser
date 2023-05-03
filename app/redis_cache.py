# pylint: disable=import-error, too-few-public-methods

"""This module contains tools for redis cache management"""

import datetime
import json
from typing import Callable

import redis
from fastapi import BackgroundTasks, Request


class RedisCacheManager:
    """Class contains attributes and methods for cache management with redis"""
    def __init__(self, host: str, port: int):
        """Instanciate a class with given redis connection parameters"""
        self.redis_client = redis.Redis(host=host, port=port)

    def set_cache(self, request_url, data, expiration: int = 300):
        """Puts given data as cache to redis with request_url as a key and passed in
        or default (300s) expiration parameter"""
        try:
            cache = json.dumps(data, default=lambda value:
                               value.isoformat() if isinstance(value, datetime.datetime)
                               else value)
        except ValueError as error:
            return {"JSON value error": str(error)}
        except TypeError as error:
            return {"JSON type error": str(error)}
        self.redis_client.set(request_url, cache, ex=expiration)
        return {"Cache set": "Cache was successfully set"}

    def get_cache(self, request_url):
        """Gets cache from redis by passed in request_url as a key"""
        cache = self.redis_client.get(request_url)
        if cache:
            return json.loads(cache, object_hook=self.datetime_parser)
        return None

    @staticmethod
    def datetime_parser(data: dict):
        """Parses json datetime fields"""
        for key, value in data.items():
            if isinstance(value, str) and value.endswith('+00:00'):
                try:
                    data[key] = datetime.datetime.fromisoformat(value)
                except ValueError:
                    pass
        return data


cache_manager = RedisCacheManager("redis", 6379)


class CacheFactory:
    """Class contains attributes and methods for path operations cache
    handling"""
    def __init__(self,
                 db_data_getter: Callable,
                 expiration: int = 300):
        """Instanciate class with cache expiration parameter (default 300s or passed)
        and pointer to a function for data from database collecting"""
        self.expiration = expiration
        self.db_data_getter = db_data_getter

    def cache_checker(self,
                      request: Request,
                      background_tasks: BackgroundTasks,
                      *args, **kwargs):
        """Method checks whether there is a cache for request output and returns
        that cache or collects needed data from database if no suitable cache
        has been found"""
        request_url = str(request.url)
        data = cache_manager.get_cache(request_url)
        if not data:
            data = self.db_data_getter(*args, **kwargs)
            background_tasks.add_task(cache_manager.set_cache,
                                      request_url=request_url,
                                      data=data,
                                      expiration=self.expiration)
        return data
