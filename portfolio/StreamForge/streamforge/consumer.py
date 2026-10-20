import asyncio
import json
import os

from aiokafka import AIOKafkaConsumer

from .engine import Event, StreamEngine


async def run() -> None:
    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    topic = os.getenv("KAFKA_TOPIC", "telemetry.events")
    consumer = AIOKafkaConsumer(
        topic,
        bootstrap_servers=bootstrap,
        group_id="streamforge-v1",
        enable_auto_commit=False,
    )
    engine = StreamEngine()
    await consumer.start()
    try:
        async for message in consumer:
            payload = json.loads(message.value)
            result = engine.ingest(Event(**payload))
            print(json.dumps({"event_id": payload["id"], **result}), flush=True)
            await consumer.commit()
    finally:
        await consumer.stop()


if __name__ == "__main__":
    asyncio.run(run())
