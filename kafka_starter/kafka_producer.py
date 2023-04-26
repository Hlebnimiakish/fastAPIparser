"""This module contains kafka-producer instance and parameters"""

from kafka import KafkaProducer

bootstrap_servers = ['kafka:29092']
producer = KafkaProducer(api_version=(0, 10, 1),
                         bootstrap_servers=bootstrap_servers)
