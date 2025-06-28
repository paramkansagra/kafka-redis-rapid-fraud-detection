from kafka import KafkaConsumer, KafkaProducer
import redis

import logging
import time
import json
from typing import Any

logging.basicConfig(level=logging.INFO)

kafkaConsumer: KafkaConsumer = None
kafkaProducer: KafkaProducer = None
redisConnection: redis.Redis = None

logging.info("Connecting to Kafka consumer...")
while kafkaConsumer == None:
    try:
        kafkaConsumer = KafkaConsumer(
            "transaction-ingress",
            bootstrap_servers="kafka1:9092",
            client_id="transaction_checker",
            group_id="transaction_checker",
            key_deserializer=lambda k: k.decode("utf-8"),
            value_deserializer=lambda v: json.loads(v),
        )

        logging.info("Kafka consumer Connection successful")
    except:
        time.sleep(5)
        logging.warning("Kafka consumer Connection unsuccessful...")

logging.info("Connecting to Kafka producer...")
while kafkaProducer == None:
    try:
        kafkaProducer = KafkaProducer(
            bootstrap_servers="kafka1:9092",
            key_serializer=str.encode,
            value_serializer=lambda v: json.dumps(v).encode(encoding="utf-8"),
            client_id="fraud_transaction_service",
        )

        logging.info("Kafka producer Connection successful")
    except:
        time.sleep(5)
        logging.warning("Kafka producer Connection unsuccessful...")

logging.info("Connecting to Redis...")
while redisConnection == None:
    try:
        redisConnection: redis.Redis = redis.Redis(
            host="redis",
            port=6379,
            db=0,
            decode_responses=True,
            password="hello",
        )
        logging.info("Redis Connection successful")
    except:
        time.sleep(5)
        logging.warning("Redis Connection unsuccessful...")


def transaction_checker(username: str, data: dict[str, Any]):
    transaction_amount = data["transaction_amount"]
    location = data["location"]
    current_time = data["current_time"]
    transaction_id = data["transaction_id"]
    current_location = data["location"]

    key_name = f"{username}-transaction-data"

    # now we will push this to redis
    redisConnection.lpush(
        key_name,
        json.dumps(
            {
                "transaction_amount": transaction_amount,
                "location": location,
                "time": current_time,
                "transaction_id": transaction_id,
            }
        ),
    )

    if redisConnection.exists(key_name) and redisConnection.llen(key_name) > 5:
        redisConnection.ltrim(key_name, 0, 4)

    # now we will get the data between the first and the last data and check the time
    recent_transaction = json.loads(redisConnection.lindex(key_name, 0))
    last_transaction = json.loads(redisConnection.lindex(key_name, -1))

    if recent_transaction["transaction_amount"] > 5000:
        data["fraud_transaction"] = "big transaction detected"
        kafkaProducer.send(
            "fraud-transactions",
            key=username,
            value=data,
        )
        logging.warning("big transaction detected")

    time_difference_between_transactions = (
        recent_transaction["time"] - last_transaction["time"]
    )

    if (
        time_difference_between_transactions < 300
        and recent_transaction["transaction_id"] != last_transaction["transaction_id"]
    ):  # if the time diff is less than 5 mins then rapid transactions
        data["fraud_transaction"] = "rapid transactions detected"
        kafkaProducer.send(
            "fraud-transactions",
            key=username,
            value=data,
        )
        logging.warning("rapid transactions detected")

    # now we will also check for the location
    key_name = f"{username}_last_transaction_location"
    last_transaction_location = None

    if redisConnection.exists(key_name):
        last_transaction_location = redisConnection.get(key_name)

    if (
        last_transaction_location != None
        and last_transaction_location != current_location
    ):
        data["fraud_transaction"] = "different locations detected"
        kafkaProducer.send(
            "fraud-transactions",
            key=username,
            value=data,
        )
        logging.warning("different locations detected")

    redisConnection.set(key_name, current_location)


for message in kafkaConsumer:
    key = message.key
    value = message.value

    transaction_checker(key, value)

kafkaConsumer.close()
