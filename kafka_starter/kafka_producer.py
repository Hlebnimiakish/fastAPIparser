"""This module contains kafka-producer instance and parameters"""

import time

from kafka import KafkaProducer
from kafka.future import Future

bootstrap_servers = ['kafka:29092']
producer = KafkaProducer(api_version=(0, 10, 1),
                         bootstrap_servers=bootstrap_servers)


def task_status_checker(task: Future):
    """Checks send task status and returns dict with task status data"""
    if task.is_done and task.succeeded():
        return {"Success": f"Task was delivered to consumer topic {str(task.value[0])}"}
    if not task.is_done:
        time.sleep(5)
        task_status_checker(task)
    return {"Error": f"Task was not delivered to consumer due to {str(task.exception)}"}


def task_sender_with_check(topic: str, message: bytes):
    """Sends task to kafka and returns it's checked status"""
    task = producer.send(topic, message)
    producer.flush()
    return {"Task status": str(task_status_checker(task))}
