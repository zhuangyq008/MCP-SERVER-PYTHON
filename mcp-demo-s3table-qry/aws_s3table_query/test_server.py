import pytest
import os
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from server import mcp

@pytest.fixture(autouse=True)
def setup_env_vars():
    # Set up test environment variables
    os.environ["ATHENA_CATALOG"] = "test_catalog"
    os.environ["ATHENA_DATABASE"] = "test_db"
    os.environ["ATHENA_TABLE"] = "test_table"
    os.environ["ATHENA_OUTPUT_LOCATION"] = "s3://test-bucket/results/"
    os.environ["AWS_REGION"] = "us-east-1"
    
    yield
    
    # Clean up environment variables after tests
    env_vars = [
        "ATHENA_CATALOG",
        "ATHENA_DATABASE",
        "ATHENA_TABLE",
        "ATHENA_OUTPUT_LOCATION",
        "AWS_REGION"
    ]
    for var in env_vars:
        os.environ.pop(var, None)

@pytest.fixture
def mock_athena_client():
    mock_client = MagicMock()
    
    # Mock start_query_execution
    mock_client.start_query_execution.return_value = {
        'QueryExecutionId': 'test-query-id'
    }
    
    # Mock get_query_execution
    mock_client.get_query_execution.return_value = {
        'QueryExecution': {
            'Status': {
                'State': 'SUCCEEDED'
            }
        }
    }
    
    # Mock get_query_results paginator
    mock_paginator = MagicMock()
    mock_paginator.paginate.return_value = [{
        'ResultSet': {
            'ResultSetMetadata': {
                'ColumnInfo': [
                    {'Name': 'bucket'},
                    {'Name': 'key'},
                    {'Name': 'record_type'},
                    {'Name': 'size'}
                ]
            },
            'Rows': [
                # Header row
                {'Data': [
                    {'VarCharValue': 'bucket'},
                    {'VarCharValue': 'key'},
                    {'VarCharValue': 'record_type'},
                    {'VarCharValue': 'size'}
                ]},
                # Data rows
                {'Data': [
                    {'VarCharValue': 'test-bucket'},
                    {'VarCharValue': 'test/key1'},
                    {'VarCharValue': 'PUT'},
                    {'VarCharValue': '1024'}
                ]},
                {'Data': [
                    {'VarCharValue': 'test-bucket'},
                    {'VarCharValue': 'test/key2'},
                    {'VarCharValue': 'GET'},
                    {'VarCharValue': '2048'}
                ]}
            ]
        }
    }]
    mock_client.get_paginator.return_value = mock_paginator
    
    return mock_client

@pytest.fixture
def server(mock_athena_client):
    with patch("boto3.client", return_value=mock_athena_client):
        from server import initialize
        initialize()
        return mcp

def test_query_record(server):
    result = server.query_record(
        start_time="2023-01-01T00:00:00",
        end_time="2023-01-02T00:00:00",
        bucket="test-bucket",
        record_type="PUT"
    )
    
    assert len(result) == 2
    assert result[0]["bucket"] == "test-bucket"
    assert result[0]["key"] == "test/key1"

def test_query_statistics(server):
    result = server.query_statistics(
        group_by=["bucket"],
        start_time="2023-01-01T00:00:00",
        end_time="2023-01-02T00:00:00"
    )
    
    assert len(result) == 2

def test_build_where_clause(server):
    where_clause = server.build_where_clause(
        start_time="2023-01-01T00:00:00",
        bucket="test-bucket",
        record_type="PUT"
    )
    
    assert "record_timestamp >= '2023-01-01T00:00:00'" in where_clause
    assert "bucket = 'test-bucket'" in where_clause
    assert "record_type = 'PUT'" in where_clause

def test_invalid_group_by(server):
    with pytest.raises(ValueError):
        server.query_statistics(
            group_by=["invalid_field"],
            start_time="2023-01-01T00:00:00"
        )

def test_missing_env_vars():
    # Remove required environment variables
    os.environ.pop("ATHENA_DATABASE", None)
    os.environ.pop("ATHENA_TABLE", None)
    
    with pytest.raises(ValueError) as exc_info:
        from server import initialize
        initialize()
    
    assert "Missing required environment variables" in str(exc_info.value)

def test_failed_query(server, mock_athena_client):
    # Mock a failed query
    mock_athena_client.get_query_execution.return_value = {
        'QueryExecution': {
            'Status': {
                'State': 'FAILED',
                'StateChangeReason': 'Test failure'
            }
        }
    }
    
    with pytest.raises(Exception) as exc_info:
        server.query_record(bucket="test-bucket")
    
    assert "failed with state FAILED" in str(exc_info.value)

