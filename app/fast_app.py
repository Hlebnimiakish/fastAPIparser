# pylint: skip-file

"""This module contains FastAPI app and it's APIs methods"""

from fastapi import FastAPI

from app.lamoda_router import lamoda_router
from app.twitch_router import twitch_router

app = FastAPI()

app.include_router(lamoda_router)
app.include_router(twitch_router)
