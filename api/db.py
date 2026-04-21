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


def get_audit_logs(limit=20):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT id, timestamp, service_name, request_id, action_performed, status, source
    FROM audit_logs
    ORDER BY id DESC
    LIMIT %s
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()

    cursor.close()
    connection.close()
    return rows


def get_request_states(limit=20):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT id, request_id, state, service_name, timestamp
    FROM request_states
    ORDER BY id DESC
    LIMIT %s
    """
    cursor.execute(query, (limit,))
    rows = cursor.fetchall()

    cursor.close()
    connection.close()
    return rows


def get_dashboard_summary():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    summary = {}

    cursor.execute("SELECT COUNT(*) AS total_requests FROM request_states")
    summary["total_states"] = cursor.fetchone()["total_requests"]

    cursor.execute("SELECT COUNT(*) AS total_logs FROM audit_logs")
    summary["total_logs"] = cursor.fetchone()["total_logs"]

    cursor.execute("SELECT COUNT(*) AS total_processed FROM request_states WHERE state = 'PROCESSED'")
    summary["processed"] = cursor.fetchone()["total_processed"]

    cursor.execute("SELECT COUNT(*) AS total_failed FROM request_states WHERE state = 'FAILED'")
    summary["failed"] = cursor.fetchone()["total_failed"]

    cursor.execute("SELECT COUNT(*) AS total_queued FROM request_states WHERE state = 'QUEUED'")
    summary["queued"] = cursor.fetchone()["total_queued"]

    cursor.close()
    connection.close()
    return summary