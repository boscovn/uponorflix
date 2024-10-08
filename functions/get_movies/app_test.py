from app import handle_get_movies, lambda_handler
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
            region_name="us-west-2",
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
        table.put_item(
            Item={"id": "1", "year": 2021, "genre": "comedy", "title": "test"}
        )
        table.put_item(
            Item={"id": "2", "year": 2022, "genre": "drama", "title": "test2"}
        )
        table.put_item(
            Item={"id": "3", "year": 2023, "genre": "comedy", "title": "test3"}
        )
        table.put_item(
            Item={"id": "4", "year": 2024, "genre": "action", "title": "test4"}
        )
        yield table
        table.delete()


def test_get_movies(table):
    event = {
        "queryStringParameters": {
            "genre": "comedy",
        }
    }
    context = MagicMock()
    response = handle_get_movies(event, context, table)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert len(body["movies"]) == 2
    assert body["movies"][0]["genre"] == "comedy"
    assert body["movies"][1]["genre"] == "comedy"
    assert body["last_evaluated_key"] is None


def test_get_movies_year_range(table):
    event = {
        "queryStringParameters": {
            "year_start": "2022",
            "year_end": "2023",
        }
    }
    context = MagicMock()
    response = handle_get_movies(event, context, table)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert len(body["movies"]) == 2
    assert body["last_evaluated_key"] is None


def test_get_movies_other_year_range(table):
    event = {
        "queryStringParameters": {
            "year_start": "2021",
            "year_end": "2023",
        }
    }
    context = MagicMock()
    response = handle_get_movies(event, context, table)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert len(body["movies"]) == 3
    assert body["last_evaluated_key"] is None


def test_get_movies_action_genre(table):
    event = {
        "queryStringParameters": {
            "genre": "action",
        }
    }
    context = MagicMock()
    response = handle_get_movies(event, context, table)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert len(body["movies"]) == 1
    assert body["movies"][0]["genre"] == "action"
    assert body["last_evaluated_key"] is None


def test_get_movies_invalid_limit(table):
    event = {
        "queryStringParameters": {
            "limit": "101",
        }
    }
    context = MagicMock()
    response = handle_get_movies(event, context, table)
    assert response["statusCode"] == 400


def test_get_movies_invalid_year(table):
    event = {
        "queryStringParameters": {
            "year_start": "2021",
            "year_end": "invalid",
        }
    }
    context = MagicMock()
    response = handle_get_movies(event, context, table)
    assert response["statusCode"] == 400


def test_get_movies_key_pagination(table):
    event = {
        "queryStringParameters": {
            "limit": "1",
        }
    }
    context = MagicMock()
    response = handle_get_movies(event, context, table)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert len(body["movies"]) == 1
    title = body["movies"][0]["title"]
    assert body["last_evaluated_key"] is not None
    last_evaluated_key = body["last_evaluated_key"]
    event["queryStringParameters"]["start_key"] = last_evaluated_key["id"]
    response = handle_get_movies(event, context, table)
    body = json.loads(response["body"])
    assert response["statusCode"] == 200
    assert len(body["movies"]) == 1
    assert body["movies"][0]["title"] != title


@patch("app.handle_get_movies")
@patch("app.table")
@patch("app.logger")
def test_lambda_handler(mock_logger, mock_table, mock_handle_get_movies):
    _ = mock_table
    mock_handle_get_movies.return_value = 5000
    response = lambda_handler(MagicMock(), MagicMock())
    assert response == 5000
    mock_logger.error.assert_not_called()
    mock_handle_get_movies.assert_called_once()


@patch("app.handle_get_movies")
@patch("app.table")
@patch("app.logger")
def test_lambda_handler_fail(mock_logger, mock_table, mock_handle_get_movies):
    _ = mock_table
    mock_handle_get_movies.side_effect = Exception("An error occurred")
    response = lambda_handler(MagicMock(), MagicMock())
    assert response["statusCode"] == 500
    mock_logger.error.assert_called_once()
    mock_handle_get_movies.assert_called_once()
