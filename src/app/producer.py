from aiokafka import AIOKafkaProducer
import os
import logging
import json
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
KAFKA_BROKER = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
logger.info(f"Connecting to Kafka at: {KAFKA_BROKER}")
KAFKA_TOPIC = 'ivashko_topic_face_verification'

class Producer:
    def __init__(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=KAFKA_BROKER)

    async def start(self):
        await self.producer.start()

    async def send(self, topic, key, value):
        logger.info(f"Sending message to topic {topic} with key {key} and value {value}")
        json_value = json.dumps(value, ensure_ascii=False)
        await self.producer.send_and_wait(topic, key=key.encode('utf-8'), value=json_value.encode('utf-8'))
        logger.info(f"Message sent to topic {topic} with key {key}")

    async def process_message(self, message):
        logger.info(f"Received message: {message.value.decode()}")

    async def stop(self):
        await self.producer.stop()
