import os
import json
import time

from db import log_audit, log_state
from rabbitmq import get_rabbitmq_connection, QUEUE_NAME

WORKER_NAME = "worker"


def process_task(task_data):
    print(f"Processing task: {task_data}")
    time.sleep(2)


def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        request_id = message.get("request_id")
        task_data = message.get("task_data")
        service_token = message.get("service_token")
        source_service = message.get("source_service", "unknown")

        expected_token = os.getenv("SERVICE_TOKEN", "internal-service-secret")

        if service_token != expected_token:
            log_audit(WORKER_NAME, request_id, "Service identity validation failed", "failure", source_service)
            log_state(request_id, "FAILED", WORKER_NAME)
            print("Invalid service token. Rejecting message.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        log_audit(WORKER_NAME, request_id, "Task consumed from RabbitMQ", "success", source_service)
        log_state(request_id, "CONSUMED", WORKER_NAME)

        process_task(task_data)

        log_audit(WORKER_NAME, request_id, "Task processed successfully", "success", source_service)
        log_state(request_id, "PROCESSED", WORKER_NAME)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Worker processing failed: {e}")
        try:
            request_id = message.get("request_id", "unknown")
            source_service = message.get("source_service", "unknown")
            log_audit(WORKER_NAME, request_id, f"Processing failed: {str(e)}", "failure", source_service)
            log_state(request_id, "FAILED", WORKER_NAME)
        except Exception as inner_error:
            print(f"Failed to log worker error: {inner_error}")

        ch.basic_ack(delivery_tag=method.delivery_tag)


def start_worker():
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print("Worker is waiting for messages...")
    channel.start_consuming()


if __name__ == "__main__":
    start_worker()