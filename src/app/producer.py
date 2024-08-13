from aiokafka import AIOKafkaProducer
import os

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
KAFKA_TOPIC = 'face_verification'

class Producer:
    def __init__(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)

    async def start(self):
        await self.producer.start()

    async def send(self, topic, key, value):
        await self.producer.send_and_wait(topic, key=key.encode('utf-8'), value=value.encode('utf-8'))

    async def stop(self):
        await self.producer.stop()
