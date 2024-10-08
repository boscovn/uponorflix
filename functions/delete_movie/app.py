import simplejson as json
import boto3
import os
import logging

logger = logging.getLogger()

if os.getenv("AWS_SAM_LOCAL"):
    dynamodb = boto3.resource("dynamodb", endpoint_url="http://dynamodb-local:8000")
else:
    dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("Movies")


def error_response(status_code, message):
    return {
        "statusCode": status_code,
        "body": json.dumps({"error": message}),
        "headers": {
            "Content-Type": "application/json",
        },
    }


def handle_delete_movie(event, context, table):
    movie_id = event["pathParameters"]["id"]
    table.delete_item(Key={"id": movie_id})
    return {"statusCode": 204}


def lambda_handler(event, context):
    try:
        return handle_delete_movie(event, context, table)
    except Exception as e:
        logger.error(
            f"An error occurred: {str(e)} with event: {event} and context: {context}"
        )
        return error_response(500, "An error occurred")
