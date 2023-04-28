# pylint: disable=import-error, too-few-public-methods

"""This module contains twitch data scraping tools"""

from enum import Enum

import requests

from app.database import CollectionHandler
from app.schema import TwitchChannel, TwitchGame, TwitchStream
from app.settings import settings

session = requests.Session()
twitch_db_name = settings.twitch_db_name


class Authorization:
    """Class contains twitch authorization data and methods"""
    def __init__(self):
        """Create instance of a class with current actual authorization data from
        settings"""
        self.client_id = settings.client_id
        grant_type = "client_credentials"
        auth_url = APIURLs.POST_AUTH.value
        self.url = auth_url + "?" \
                            + f"client_id={self.client_id}" \
                            + f"&client_secret={settings.secret_key}" \
                            + f"&grant_type={grant_type}"

    def get_headers(self):
        """Generates and returns headers for twitch api use (with class auth data)"""
        response = session.post(self.url)
        token = response.json()['access_token']
        headers = {"Authorization": f"Bearer {token}",
                   "Client-Id": self.client_id}
        return headers


class APIURLs(Enum):
    """Class contains twitch API methods"""
    POST_AUTH = "https://id.twitch.tv/oauth2/token"
    GET_GAMES = 'https://api.twitch.tv/helix/games/top'
    GET_CHANNELS = 'https://api.twitch.tv/helix/channels'
    GET_STREAMS = 'https://api.twitch.tv/helix/streams'


class TwitchCollections(Enum):
    """Class contains mongodb twitch CollectionHandler class instances"""
    GAMES = CollectionHandler(twitch_db_name, "twitch_games")
    STREAMS = CollectionHandler(twitch_db_name, "twitch_streams")
    CHANNELS = CollectionHandler(twitch_db_name, "twitch_channels")


class TwitchParserTools:
    """Class contains tools for twitch data scraping with twitch API"""
    headers = Authorization().get_headers()
    urls = APIURLs
    collections = TwitchCollections

    @classmethod
    def collect_top_games(cls, cursor: str | None = None):
        """Gets and puts in database current top twitch games (recursively calls itself
        if there are more games to get)"""
        url = cls.urls.GET_GAMES.value
        if cursor:
            url = url + f'?after={cursor}'
        response = session.get(url, headers=cls.headers, timeout=300)
        response_data = response.json()
        games = response_data['data']
        if games:
            for game in games:
                game = TwitchGame.twitch_game_data_creator(game['id'],
                                                           game['name'])
                cls.collections.GAMES.value.insert_one(game)
        if response_data['pagination']:
            cursor = response.json()['pagination']['cursor']
            cls.collect_top_games(cursor)

    @classmethod
    def collect_channels(cls):
        """Gets and puts to the database all channels of stored in
        database broadcasters (streamers)"""
        for stream in cls.collections.STREAMS.value.find({}, ['user_id']):
            broadcaster = stream['user_id']
            channel_url = cls.urls.GET_CHANNELS.value + f'?broadcaster_id={broadcaster}'
            response = session.get(channel_url, headers=cls.headers, timeout=300)
            channels_data = response.json()['data']
            for channel_data in channels_data:
                channel = TwitchChannel.twitch_channel_data_creation(channel_data)
                cls.collections.CHANNELS.value.insert_one(channel)

    @classmethod
    def collect_streams(cls):
        """Gets and passes to stream_collector function stored
        in database game instances"""
        for game in cls.collections.GAMES.value.find({}, ['game_id']):
            game_id = game["game_id"]
            cls.stream_collector(game_id)

    @classmethod
    def stream_collector(cls, game_id: str, cursor: str | None = None):
        """Gets and puts in database all streams for passed in game (recursively calls itself
        if there are more streams to get)"""
        url = cls.urls.GET_STREAMS.value + f"?game_id={game_id}"
        if cursor:
            url = url + f"&after={cursor}"
        response = session.get(url,
                               headers=cls.headers,
                               timeout=300)
        response_data = response.json()
        streams = response.json()['data']
        if streams:
            for stream in streams:
                stream_data = TwitchStream.twitch_stream_data_creator(stream)
                cls.collections.STREAMS.value.insert_one(stream_data)
        if response_data['pagination']:
            cursor = response.json()['pagination']['cursor']
            cls.stream_collector(game_id, cursor)


class TwitchParser:
    """Class contains methods needed for twitch data collection"""
    def __init__(self):
        self.collect_top_games = TwitchParserTools.collect_top_games
        self.collect_streams = TwitchParserTools.collect_streams
        self.collect_channels = TwitchParserTools.collect_channels

    @classmethod
    def parse_twitch_data(cls):
        """Calls needed twitch data collection methods in the right order,
        cleaning collections data before getting new"""
        created_parser = TwitchParser()
        TwitchParserTools.collections.GAMES.value.delete_many({})
        created_parser.collect_top_games()
        TwitchParserTools.collections.STREAMS.value.delete_many({})
        created_parser.collect_streams()
        TwitchParserTools.collections.CHANNELS.value.delete_many({})
        created_parser.collect_channels()
