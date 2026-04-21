import os
import json
import time
import pika


QUEUE_NAME = "task_queue"


def get_rabbitmq_connection():
    for _ in range(10):
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "rabbitmq"))
            )
            return connection
        except Exception as e:
            print(f"RabbitMQ connection failed: {e}")
            time.sleep(5)
    raise Exception("Could not connect to RabbitMQ after multiple attempts")


def publish_message(message):
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2
        )
    )

    print(f"Message published to RabbitMQ: {message}")

    connection.close()