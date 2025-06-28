from kafka.admin import KafkaAdminClient, NewTopic
import logging
import time

logging.basicConfig(level=logging.INFO)

kafkaAdminClient = None

logging.info("Connecting to kafka...")

while kafkaAdminClient == None:
    try:
        kafkaAdminClient = KafkaAdminClient(
            bootstrap_servers="kafka1:9092",
            client_id="transaction-service-admin",
        )

        logging.info("Connection to kafka successful...")
    except:
        time.sleep(5)
        logging.warning("Connection to kafka unsuccessful...")

newTopicList = []
newTopicList.append(
    NewTopic(
        name="transaction-ingress",
        num_partitions=5,
        replication_factor=1,
    ),
)
newTopicList.append(
    NewTopic(
        name="fraud-transactions",
        num_partitions=5,
        replication_factor=1,
    ),
)

logging.info("Creating new topics...")
kafkaAdminClient.create_topics(new_topics=newTopicList)
logging.info("Topic created successfully")

kafkaAdminClient.close()
