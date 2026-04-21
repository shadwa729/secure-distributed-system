import os
import time
import mysql.connector


def get_db_connection():
    for _ in range(10):
        try:
            connection = mysql.connector.connect(
                host=os.getenv("MYSQL_HOST", "mysql"),
                user=os.getenv("MYSQL_USER", "appuser"),
                password=os.getenv("MYSQL_PASSWORD", "apppassword"),
                database=os.getenv("MYSQL_DATABASE", "auditdb")
            )
            return connection
        except Exception as e:
            print(f"Database connection failed: {e}")
            time.sleep(5)
    raise Exception("Could not connect to MySQL after multiple attempts")


def log_audit(service_name, request_id, action_performed, status, source):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO audit_logs (service_name, request_id, action_performed, status, source)
    VALUES (%s, %s, %s, %s, %s)
    """
    values = (service_name, request_id, action_performed, status, source)

    cursor.execute(query, values)
    connection.commit()

    cursor.close()
    connection.close()


def log_state(request_id, state, service_name):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO request_states (request_id, state, service_name)
    VALUES (%s, %s, %s)
    """
    values = (request_id, state, service_name)

    cursor.execute(query, values)
    connection.commit()

    cursor.close()
    connection.close()