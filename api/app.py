import os
import uuid
from flask import Flask, request, jsonify, render_template_string

from db import (
    log_audit,
    log_state,
    get_audit_logs,
    get_request_states,
    get_dashboard_summary
)
from auth import validate_jwt
from rabbitmq import publish_message

app = Flask(__name__)

INSTANCE_NAME = os.getenv("INSTANCE_NAME", "api")


DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>System Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1, h2 {
            color: #222;
        }
        .cards {
            display: flex;
            gap: 15px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }
        .card {
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            min-width: 180px;
        }
        .card h3 {
            margin: 0 0 10px 0;
            font-size: 16px;
        }
        .card p {
            font-size: 22px;
            margin: 0;
            font-weight: bold;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        th, td {
            border: 1px solid #ddd;
            padding: 10px;
            text-align: left;
            font-size: 14px;
        }
        th {
            background-color: #222;
            color: white;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .section-title {
            margin-top: 30px;
        }
    </style>
</head>
<body>
    <h1>Secure Distributed System Dashboard</h1>
    <p><strong>Served by:</strong> {{ instance_name }}</p>

    <div class="cards">
        <div class="card">
            <h3>Total Logs</h3>
            <p>{{ summary.total_logs }}</p>
        </div>
        <div class="card">
            <h3>Total States</h3>
            <p>{{ summary.total_states }}</p>
        </div>
        <div class="card">
            <h3>Processed</h3>
            <p>{{ summary.processed }}</p>
        </div>
        <div class="card">
            <h3>Failed</h3>
            <p>{{ summary.failed }}</p>
        </div>
        <div class="card">
            <h3>Queued</h3>
            <p>{{ summary.queued }}</p>
        </div>
    </div>

    <h2 class="section-title">Recent Audit Logs</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Timestamp</th>
            <th>Service</th>
            <th>Request ID</th>
            <th>Action</th>
            <th>Status</th>
            <th>Source</th>
        </tr>
        {% for row in audit_logs %}
        <tr>
            <td>{{ row.id }}</td>
            <td>{{ row.timestamp }}</td>
            <td>{{ row.service_name }}</td>
            <td>{{ row.request_id }}</td>
            <td>{{ row.action_performed }}</td>
            <td>{{ row.status }}</td>
            <td>{{ row.source }}</td>
        </tr>
        {% endfor %}
    </table>

    <h2 class="section-title">Recent Request States</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Request ID</th>
            <th>State</th>
            <th>Service</th>
            <th>Timestamp</th>
        </tr>
        {% for row in request_states %}
        <tr>
            <td>{{ row.id }}</td>
            <td>{{ row.request_id }}</td>
            <td>{{ row.state }}</td>
            <td>{{ row.service_name }}</td>
            <td>{{ row.timestamp }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""


@app.route("/task", methods=["POST"])
def create_task():
    auth_header = request.headers.get("Authorization", "")

    if not auth_header.startswith("Bearer "):
        request_id = str(uuid.uuid4())
        log_audit(INSTANCE_NAME, request_id, "Missing or invalid Authorization header", "failure", "client")
        log_state(request_id, "FAILED", INSTANCE_NAME)
        return jsonify({"error": "Unauthorized"}), 401

    token = auth_header.split(" ")[1]
    decoded_token = validate_jwt(token)

    if not decoded_token:
        request_id = str(uuid.uuid4())
        log_audit(INSTANCE_NAME, request_id, "JWT validation failed", "failure", "client")
        log_state(request_id, "FAILED", INSTANCE_NAME)
        return jsonify({"error": "Unauthorized"}), 401

    request_id = str(uuid.uuid4())
    data = request.json if request.is_json else {}

    log_audit(INSTANCE_NAME, request_id, "Request received", "success", "client")
    log_state(request_id, "RECEIVED", INSTANCE_NAME)

    log_audit(INSTANCE_NAME, request_id, "JWT validated", "success", "client")
    log_state(request_id, "AUTHENTICATED", INSTANCE_NAME)

    message = {
        "request_id": request_id,
        "task_data": data,
        "service_token": os.getenv("SERVICE_TOKEN", "internal-service-secret"),
        "source_service": INSTANCE_NAME
    }

    publish_message(message)

    log_audit(INSTANCE_NAME, request_id, "Task sent to RabbitMQ", "success", INSTANCE_NAME)
    log_state(request_id, "QUEUED", INSTANCE_NAME)

    return jsonify({
        "message": "Task received and queued successfully",
        "request_id": request_id,
        "handled_by": INSTANCE_NAME
    }), 200


@app.route("/")
def home():
    return jsonify({
        "service": INSTANCE_NAME,
        "status": "running"
    })


@app.route("/dashboard")
def dashboard():
    summary = get_dashboard_summary()
    audit_logs = get_audit_logs()
    request_states = get_request_states()

    return render_template_string(
        DASHBOARD_HTML,
        summary=summary,
        audit_logs=audit_logs,
        request_states=request_states,
        instance_name=INSTANCE_NAME
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)