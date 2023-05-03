# pylint: skip-file

import datetime
import json
from typing import Callable

import redis
from fastapi import BackgroundTasks, Request


class RedisCacheManager:
    def __init__(self, host: str, port: int):
        self.redis_client = redis.Redis(host=host, port=port)

    def set_cache(self, request_url, data, expiration: int = 300):
        try:
            cache = json.dumps(data, default=lambda value:
                               value.isoformat() if isinstance(value, datetime.datetime)
                               else value)
        except ValueError as error:
            return {"JSON value error": str(error)}
        except TypeError as error:
            return {"JSON type error": str(error)}
        self.redis_client.set(request_url, cache, ex=expiration)

    def get_cache(self, request_url):
        cache = self.redis_client.get(request_url)
        if cache:
            return json.loads(cache, object_hook=self.datetime_parser)
        return None

    @staticmethod
    def datetime_parser(data: dict):
        for k, v in data.items():
            if isinstance(v, str) and v.endswith('+00:00'):
                try:
                    data[k] = datetime.datetime.fromisoformat(v)
                except ValueError:
                    pass
        return data


cache_manager = RedisCacheManager("redis", 6379)


class CacheFactory:
    def __init__(self,
                 db_data_getter: Callable,
                 expiration: int = 300):
        self.expiration = expiration
        self.db_data_getter = db_data_getter

    def cache_checker(self,
                      request: Request,
                      background_tasks: BackgroundTasks,
                      *args, **kwargs):
        request_url = str(request.url)
        data = cache_manager.get_cache(request_url)
        if not data:
            data = self.db_data_getter(*args, **kwargs)
            background_tasks.add_task(cache_manager.set_cache,
                                      request_url=request_url,
                                      data=data,
                                      expiration=self.expiration)
        return data
