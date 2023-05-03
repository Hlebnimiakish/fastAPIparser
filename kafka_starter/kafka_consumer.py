# pylint: disable=import-error

"""This module contains kafka-consumer instances methods and parameters"""

import json
import threading
import time

from kafka import KafkaConsumer

from app.database import CollectionHandler
from app.lamoda_scripts import (CategoryDataScraper, HomeCategoriesCollector,
                                ThePageParser)
from app.settings import settings
from app.twitch_scripts import TwitchParser

lamoda_db_name = settings.LAMODA_DB_NAME

lamoda_categories_consumer = KafkaConsumer('lamoda_category_parser',
                                           group_id='group1',
                                           bootstrap_servers=['kafka:29092'],
                                           max_poll_interval_ms=600000)

lamoda_page_consumer = KafkaConsumer('lamoda_page_parser',
                                     group_id='group1',
                                     bootstrap_servers=['kafka:29092'],
                                     max_poll_interval_ms=1800000)

lamoda_goods_consumer = KafkaConsumer('lamoda_goods_parser',
                                      group_id='group1',
                                      bootstrap_servers=['kafka:29092'],
                                      max_poll_interval_ms=900000000)

twitch_data_consumer = KafkaConsumer('twitch_data_parser',
                                     group_id='group1',
                                     bootstrap_servers=['kafka:29092'],
                                     max_poll_interval_ms=900000000)


def categories_consumer_runner():
    """This function runs loop for lamoda_categories_consumer messages processing"""
    for _ in lamoda_categories_consumer:
        collection = CollectionHandler(lamoda_db_name, "categories")
        collection.delete_many({})
        HomeCategoriesCollector().put_categories_to_db()
        time.sleep(1)


def goods_consumer_runner():
    """This function runs loop for lamoda_goods_consumer messages processing"""
    for message in lamoda_goods_consumer:
        message_data = json.loads(message.value.decode('UTF-8'))
        collection_name = \
            CategoryDataScraper.collection_name_generator(message_data["category_type"],
                                                          message_data["subcategory"])
        collection = CollectionHandler(lamoda_db_name, collection_name)
        collection.delete_many({})
        CategoryDataScraper(message_data["category_type"], message_data["subcategory"],
                            message_data["pages_to_parse_limiter"])
        time.sleep(1)


def page_consumer_runner():
    """This function runs loop for lamoda_page_consumer messages processing"""
    for message in lamoda_page_consumer:
        message_data = json.loads(message.value.decode('UTF-8'))
        ThePageParser.parse_passed_page(message_data['page_to_parse'])
        time.sleep(1)


def twitch_consumer_runner():
    """This function runs loop for twitch_data_consumer messages processing"""
    for _ in twitch_data_consumer:
        TwitchParser.parse_twitch_data()
        time.sleep(1)


if __name__ == '__main__':

    lamoda_cats_consumer_thread = threading.Thread(target=categories_consumer_runner)
    lamoda_cats_consumer_thread.start()

    lamoda_goods_consumer_thread = threading.Thread(target=goods_consumer_runner)
    lamoda_goods_consumer_thread.start()

    lamoda_page_parser_thread = threading.Thread(target=page_consumer_runner)
    lamoda_page_parser_thread.start()

    twitch_data_parser_thread = threading.Thread(target=twitch_consumer_runner)
    twitch_data_parser_thread.start()
