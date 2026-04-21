import os
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