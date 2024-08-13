from aiokafka import AIOKafkaProducer
from fastapi import HTTPException
import asyncio
import os

# KAFKA_BROKER = os.environ.get('KAFKA_BROKER', 'localhost:9092')
# KAFKA_TOPIC = 'face_verification'

# class Producer:
#     def __init__(self):
#         self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)

#     async def start(self):
#         await self.producer.start()

#     async def send(self, topic, key, value):
#         await self.producer.send_and_wait(topic, key=key.encode('utf-8'), value=value.encode('utf-8'))

#     async def stop(self):
#         await self.producer.stop()
