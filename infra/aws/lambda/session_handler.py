import json
import os
import time
import uuid

import boto3


TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "")
dynamodb = boto3.resource("dynamodb")


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    path = event.get("rawPath", "")
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")

    if path == "/health":
        return _response(200, {"status": "ok", "service": "smartspend-lambda"})

    if not TABLE_NAME:
        return _response(500, {"error": "DynamoDB table not configured"})

    table = dynamodb.Table(TABLE_NAME)

    if method == "POST" and path == "/session":
        session_id = str(uuid.uuid4())
        ttl = int(time.time()) + 86400
        table.put_item(
            Item={
                "session_id": session_id,
                "created_at": int(time.time()),
                "expires_at": ttl,
                "source": "api-gateway-lambda",
            }
        )
        return _response(200, {"session_id": session_id, "expires_at": ttl})

    if method == "GET" and path.startswith("/session/"):
        session_id = path.rsplit("/", 1)[-1]
        result = table.get_item(Key={"session_id": session_id})
        if "Item" not in result:
            return _response(404, {"error": "Session not found"})
        return _response(200, result["Item"])

    return _response(
        200,
        {
            "message": "SmartSpend serverless endpoint is active.",
            "routes": ["POST /session", "GET /session/{id}", "GET /health"],
        },
    )
