import simplejson as json
import uuid
import boto3
import os
import logging

logger = logging.getLogger()

table = None


def get_table():
    global table
    if table is None:
        if os.environ.get("AWS_SAM_LOCAL"):
            dynamodb = boto3.resource(
                "dynamodb", endpoint_url="http://dynamodb-local:8000"
            )
            table_name = "Movies"
            existing_tables = dynamodb.meta.client.list_tables()["TableNames"]
            if table_name not in existing_tables:
                table = dynamodb.create_table(
                    TableName=table_name,
                    KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
                    AttributeDefinitions=[
                        {"AttributeName": "id", "AttributeType": "S"}
                    ],
                    ProvisionedThroughput={
                        "ReadCapacityUnits": 1,
                        "WriteCapacityUnits": 1,
                    },
                )
                table.meta.client.get_waiter("table_exists").wait(TableName=table_name)
            else:
                table = dynamodb.Table(table_name)
        else:
            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table("Movies")
        return table


def error_response(status_code, message):
    return {
        "statusCode": status_code,
        "body": json.dumps({"error": message}),
        "headers": {
            "Content-Type": "application/json",
        },
    }


def handle_add_or_update_movie(event, context, table):
    body = json.loads(event["body"])
    id = body.get("id", str(uuid.uuid4()))
    title = body.get("title")
    if not title:
        return error_response(400, "Title is required")
    year = body.get("year")
    if not year:
        return error_response(400, "Year is required")

    genre = body.get("genre")
    if not genre:
        return error_response(400, "Genre is required")

    movie = {"year": year, "title": title, "id": id, "genre": genre}
    response = table.put_item(Item=movie)
    if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
        logger.error(str(response))
        return error_response(500, "An error occurred")
    return {
        "statusCode": 200,
        "body": json.dumps(movie),
    }


def lambda_handler(event, context):
    try:
        return handle_add_or_update_movie(event, context, get_table())
    except Exception as e:
        logger.error(
            f"An error occurred: {str(e)} with event: {event} and context: {context}"
        )
        return error_response(500, "An error occurred")
