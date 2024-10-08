from app import handle_delete_movie, lambda_handler
import pytest
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
        table.put_item(
            Item={"id": "1", "year": 2021, "genre": "comedy", "title": "test"}
        )
        table.put_item(
            Item={"id": "2", "year": 2022, "genre": "drama", "title": "test2"}
        )
        yield table
        table.delete()


def test_delete_movie(table):
    assert table.item_count == 2
    event = {"pathParameters": {"id": "1"}}
    response = handle_delete_movie(event, MagicMock(), table)
    assert response["statusCode"] == 204
    assert table.item_count == 1
    response = table.get_item(Key={"id": "1"})
    assert "Item" not in response
    response = table.get_item(Key={"id": "2"})
    assert "Item" in response


@patch("app.handle_delete_movie")
@patch("app.table")
@patch("app.logger")
def test_lambda_handler(mock_logger, mock_table, mock_handle_delete_movie):
    _ = mock_table
    mock_handle_delete_movie.return_value = 5000
    response = lambda_handler(MagicMock(), MagicMock())
    assert response == 5000
    mock_logger.error.assert_not_called()
    mock_handle_delete_movie.assert_called_once()


@patch("app.handle_delete_movie")
@patch("app.table")
@patch("app.logger")
def test_lambda_handler_fail(mock_logger, mock_table, mock_handle_delete_movie):
    _ = mock_table
    mock_handle_delete_movie.side_effect = Exception("An error occurred")
    response = lambda_handler(MagicMock(), MagicMock())
    assert response["statusCode"] == 500
    mock_logger.error.assert_called_once()
    mock_handle_delete_movie.assert_called_once()
