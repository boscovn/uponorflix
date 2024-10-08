import os
import boto3
import simplejson as json
from boto3.dynamodb.conditions import Attr
import logging

logger = logging.getLogger()

dynamodb = (
    boto3.resource("dynamodb", endpoint_url="http://dynamodb-local:8000")
    if os.environ.get("AWS_SAM_LOCAL")
    else boto3.resource("dynamodb")
)
table = dynamodb.Table("Movies")


def error_response(status_code, message):
    return {
        "statusCode": status_code,
        "body": json.dumps({"error": message}),
        "headers": {
            "Content-Type": "application/json",
        },
    }


def handle_get_movies(event, context, table):
    params = event.get("queryStringParameters")
    if params is None:
        params = {}
    limit = params.get("limit")
    if limit is not None:
        try:
            limit = int(limit)
        except ValueError:
            return error_response(400, "Limit must be an integer")
        if limit < 1 or limit > 100:
            return error_response(400, "Limit must be between 1 and 100")
    else:
        limit = 10
    year_start = params.get("year_start", 0)
    year_end = params.get("year_end", 3000)
    try:
        year_start = int(year_start)
        year_end = int(year_end)
    except ValueError:
        return error_response(400, "Year must be an integer")
    filter_expression = Attr("year").between(year_start, year_end)
    genre = params.get("genre", None)
    if genre:
        filter_expression = filter_expression & Attr("genre").eq(genre)
    start_key = params.get("start_key")
    if start_key:
        response = table.scan(
            Limit=limit,
            FilterExpression=filter_expression,
            ExclusiveStartKey={"id": start_key},
        )
    else:
        response = table.scan(Limit=limit, FilterExpression=filter_expression)
    movies = response.get("Items", [])
    last_evaluated_key = response.get("LastEvaluatedKey", None)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {"movies": movies, "last_evaluated_key": last_evaluated_key}
        ),
        "headers": {
            "Content-Type": "application/json",
        },
    }


def lambda_handler(event, context):
    try:
        return handle_get_movies(event, context, table)
    except Exception as e:
        logger.error(e)
        return error_response(500, "Internal server error")
