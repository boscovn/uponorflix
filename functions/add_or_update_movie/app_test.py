from app import lambda_handler, handle_add_or_update_movie
import pytest
import simplejson as json
from unittest.mock import MagicMock, patch

from testcontainers.core.container import DockerContainer
from testcontainers.core.waiting_utils import wait_for_logs
import boto3


@pytest.fixture
def table():
    with DockerContainer("amazon/dynamodb-local:2.5.0") as dynamodb:
        dynamodb.with_exposed_ports(8000)
        dynamodb.start()
        port = dynamodb.get_exposed_port(8000)
        wait_for_logs(dynamodb, "Version:")
        endpoint = f"http://localhost:{port}"
        client = boto3.resource(
            "dynamodb",
            endpoint_url=endpoint,
        )
        table = client.create_table(
            TableName="Movies",
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "id", "AttributeType": "S"},
            ],
            ProvisionedThroughput={
                "ReadCapacityUnits": 1,
                "WriteCapacityUnits": 1,
            },
        )
        yield table
        table.delete()


def test_fixure_works(table):
    table.put_item(
        Item={
            "id": "1",
            "title": "The Shawshank Redemption",
            "year": 1994,
            "genre": "Drama",
        }
    )
    response = table.get_item(Key={"id": "1"})
    assert response["Item"]["title"] == "The Shawshank Redemption"
    assert response["Item"]["year"] == 1994
    assert response["Item"]["genre"] == "Drama"


def test_add_movie(table):
    event = {
        "body": json.dumps(
            {
                "title": "The Shawshank Redemption",
                "year": 1994,
                "genre": "Drama",
            }
        ),
    }
    response = handle_add_or_update_movie(event, None, table)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["title"] == "The Shawshank Redemption"
    assert body["year"] == 1994
    assert body["genre"] == "Drama"
    id = body["id"]
    response = table.get_item(Key={"id": id})
    assert response["Item"]["title"] == "The Shawshank Redemption"
    assert response["Item"]["year"] == 1994
    assert response["Item"]["genre"] == "Drama"


def test_add_movie_missing_title(table):
    event = {
        "body": json.dumps(
            {
                "year": 1994,
                "genre": "Drama",
            }
        ),
    }
    response = handle_add_or_update_movie(event, None, table)
    assert response["statusCode"] == 400


def test_add_movie_missing_year(table):
    event = {
        "body": json.dumps(
            {
                "title": "The Shawshank Redemption",
                "genre": "Drama",
            }
        ),
    }
    response = handle_add_or_update_movie(event, None, table)
    assert response["statusCode"] == 400


def test_add_movie_missing_genre(table):
    event = {
        "body": json.dumps(
            {
                "title": "The Shawshank Redemption",
                "year": 1994,
            }
        ),
    }
    response = handle_add_or_update_movie(event, None, table)
    assert response["statusCode"] == 400


def test_update_movie(table):
    event = {
        "body": json.dumps(
            {
                "title": "The Shawshank Redemption",
                "year": 1994,
                "genre": "Drama",
            }
        ),
    }
    response = handle_add_or_update_movie(event, None, table)
    body = json.loads(response["body"])
    id = body["id"]
    event = {
        "body": json.dumps(
            {
                "id": id,
                "title": "The Godfather",
                "year": 1972,
                "genre": "Crime",
            }
        ),
    }
    response = handle_add_or_update_movie(event, None, table)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["title"] == "The Godfather"
    assert body["year"] == 1972
    assert body["genre"] == "Crime"
    response = table.get_item(Key={"id": id})
    assert response["Item"]["title"] == "The Godfather"
    assert response["Item"]["year"] == 1972
    assert response["Item"]["genre"] == "Crime"


def test_table_failure():
    table = MagicMock()
    table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 500}}
    event = {
        "body": json.dumps(
            {
                "title": "The Shawshank Redemption",
                "year": 1994,
                "genre": "Drama",
            }
        ),
    }
    response = handle_add_or_update_movie(event, None, table)
    assert response["statusCode"] == 500
