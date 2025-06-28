from flask import Flask, request, make_response, jsonify
from kafka import KafkaProducer

import time
from json import dumps
from uuid import uuid4
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

kafkaProducer = None

logging.info("Trying to connect to kafka service...")
while kafkaProducer == None:
    try:
        kafkaProducer = KafkaProducer(
            bootstrap_servers="kafka1:9092",
            key_serializer=str.encode,
            value_serializer=lambda v: dumps(v).encode(encoding="utf-8"),
            client_id="transaction_ingress_service",
        )
        logging.info("Connection successful...")
    except:
        time.sleep(5)
        logging.warning("No nodes avaliable trying again in 5 seconds...")


@app.route("/create_transaction", methods=["POST"])
def create_transaction():
    try:
        user_name = request.form["user_name"]
        transaction_amount = float(request.form["transaction_amount"])
        location = request.form["transaction_location"]
        current_time = int(time.time())

        transaction_id = str(uuid4())

        # push all this to kafka and we can proceed from there

        data = {
            "user_name": user_name,
            "transaction_amount": transaction_amount,
            "location": location,
            "current_time": current_time,
            "transaction_id": transaction_id,
        }

        kafkaProducer.send(topic="transaction-ingress", key=user_name, value=data)

        return jsonify(data), 200

    except Exception as err:
        error_json = jsonify(
            {
                "error": str(err),
            }
        )
        return make_response(
            error_json,
            400,
        )


if __name__ == "__main__":
    app.run(
        debug=True,
        port=4000,
        host="0.0.0.0",
    )
