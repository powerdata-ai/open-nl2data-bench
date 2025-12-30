"""Unit tests for HTTP SUT adapter."""
import pytest
from unittest.mock import MagicMock, patch, Mock
import httpx

import pandas as pd

from onb.adapters.sut.http import HTTPSUTAdapter
from onb.core.exceptions import SUTAdapterError
from onb.core.types import (
    ColumnInfo,
    SchemaInfo,
    SUTConfig,
    TableInfo,
    DatabaseType,
)


@pytest.fixture
def basic_config():
    """Basic HTTP SUT configuration."""
    return SUTConfig(
        name="TestHTTPSUT",
        type="http",
        version="1.0.0",
        config={
            "api_url": "https://api.example.com/nl2sql",
            "method": "POST",
            "auth_type": "none",
            "timeout": 30.0,
        },
    )


@pytest.fixture
def bearer_auth_config():
    """HTTP SUT configuration with Bearer token."""
    return SUTConfig(
        name="TestHTTPSUT",
        type="http",
        version="1.0.0",
        config={
            "api_url": "https://api.example.com/nl2sql",
            "auth_type": "bearer",
            "auth_token": "test-token-123",
        },
    )


@pytest.fixture
def api_key_config():
    """HTTP SUT configuration with API key."""
    return SUTConfig(
        name="TestHTTPSUT",
        type="http",
        version="1.0.0",
        config={
            "api_url": "https://api.example.com/nl2sql",
            "auth_type": "api_key",
            "api_key": "test-api-key-456",
        },
    )


@pytest.fixture
def custom_mapping_config():
    """HTTP SUT configuration with custom field mapping."""
    return SUTConfig(
        name="TestHTTPSUT",
        type="http",
        version="1.0.0",
        config={
            "api_url": "https://api.example.com/nl2sql",
            "request_mapping": {
                "question_key": "query",
                "schema_key": "db_schema",
                "language_key": "lang",
            },
            "response_mapping": {
                "sql_key": "generated_query",
                "data_key": "results",
                "error_key": "error_msg",
            },
        },
    )


@pytest.fixture
def sample_schema():
    """Sample database schema."""
    return SchemaInfo(
        database_name="test_db",
        database_type=DatabaseType.MYSQL,
        tables=[
            TableInfo(
                name="users",
                columns=[
                    ColumnInfo(name="id", type="int", primary_key=True),
                    ColumnInfo(name="name", type="varchar"),
                ],
            )
        ],
    )


class TestHTTPSUTAdapter:
    """Test HTTPSUTAdapter class."""

    def test_initialization(self, basic_config):
        """Test adapter initialization."""
        adapter = HTTPSUTAdapter(basic_config)
        assert adapter.api_url == "https://api.example.com/nl2sql"
        assert adapter.method == "POST"
        assert adapter.timeout == 30.0
        assert adapter.auth_type == "none"

    def test_initialization_without_api_url(self):
        """Test initialization fails without API URL."""
        config = SUTConfig(
            name="TestHTTPSUT",
            type="http",
            version="1.0.0",
            config={},
        )

        adapter = HTTPSUTAdapter(config)

        with pytest.raises(SUTAdapterError, match="api_url is required"):
            adapter.initialize()

    def test_build_headers_no_auth(self, basic_config):
        """Test building headers without authentication."""
        adapter = HTTPSUTAdapter(basic_config)
        headers = adapter._build_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert "Authorization" not in headers
        assert "X-API-Key" not in headers

    def test_build_headers_bearer_auth(self, bearer_auth_config):
        """Test building headers with Bearer token."""
        adapter = HTTPSUTAdapter(bearer_auth_config)
        headers = adapter._build_headers()

        assert headers["Authorization"] == "Bearer test-token-123"

    def test_build_headers_api_key(self, api_key_config):
        """Test building headers with API key."""
        adapter = HTTPSUTAdapter(api_key_config)
        headers = adapter._build_headers()

        assert headers["X-API-Key"] == "test-api-key-456"

    def test_build_headers_custom(self):
        """Test building headers with custom headers."""
        config = SUTConfig(
            name="TestHTTPSUT",
            type="http",
            version="1.0.0",
            config={
                "api_url": "https://api.example.com/nl2sql",
                "headers": {
                    "X-Custom-Header": "custom-value",
                    "X-Request-ID": "12345",
                },
            },
        )

        adapter = HTTPSUTAdapter(config)
        headers = adapter._build_headers()

        assert headers["X-Custom-Header"] == "custom-value"
        assert headers["X-Request-ID"] == "12345"

    def test_build_request_payload_default(self, basic_config, sample_schema):
        """Test building request payload with default mapping."""
        adapter = HTTPSUTAdapter(basic_config)
        payload = adapter._build_request_payload(
            "How many users?", sample_schema, "en", {}
        )

        assert payload["question"] == "How many users?"
        assert payload["schema"] == sample_schema.to_dict()
        assert payload["language"] == "en"

    def test_build_request_payload_custom_mapping(
        self, custom_mapping_config, sample_schema
    ):
        """Test building request payload with custom mapping."""
        adapter = HTTPSUTAdapter(custom_mapping_config)
        payload = adapter._build_request_payload(
            "Count users", sample_schema, "zh", {}
        )

        assert payload["query"] == "Count users"
        assert payload["db_schema"] == sample_schema.to_dict()
        assert payload["lang"] == "zh"

    @patch("httpx.Client")
    def test_query_success(self, mock_client_class, basic_config, sample_schema):
        """Test successful query execution."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "sql": "SELECT COUNT(*) FROM users",
            "data": [{"count": 42}],
        }
        mock_response.raise_for_status = Mock()

        # Setup mock client
        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Execute query
        adapter = HTTPSUTAdapter(basic_config)
        adapter.initialize()

        result = adapter.query("How many users?", sample_schema)

        # Verify result
        assert result.success is True
        assert result.generated_sql == "SELECT COUNT(*) FROM users"
        assert result.result_dataframe is not None
        assert len(result.result_dataframe) == 1
        assert result.result_dataframe.iloc[0]["count"] == 42

        # Verify HTTP call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "https://api.example.com/nl2sql"

    @patch("httpx.Client")
    def test_query_with_error_response(
        self, mock_client_class, basic_config, sample_schema
    ):
        """Test query with error in API response."""
        # Setup mock response with error
        mock_response = Mock()
        mock_response.json.return_value = {
            "sql": "",
            "error": "Invalid question format",
        }
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = HTTPSUTAdapter(basic_config)
        adapter.initialize()

        result = adapter.query("Bad question", sample_schema)

        assert result.success is False
        assert "Invalid question format" in result.error

    @patch("httpx.Client")
    def test_query_http_error_with_retry(
        self, mock_client_class, basic_config, sample_schema
    ):
        """Test query with HTTP error and retry mechanism."""
        # Setup mock client to fail then succeed
        mock_client = Mock()
        mock_client.post.side_effect = [
            httpx.ConnectError("Connection failed"),
            httpx.ConnectError("Connection failed"),
            Mock(
                json=lambda: {"sql": "SELECT 1", "data": []},
                raise_for_status=Mock(),
            ),
        ]
        mock_client_class.return_value = mock_client

        adapter = HTTPSUTAdapter(basic_config)
        adapter.retry_count = 3
        adapter.retry_delay = 0.01  # Fast retry for testing
        adapter.initialize()

        result = adapter.query("Test", sample_schema)

        # Should succeed after retries
        assert result.success is True
        assert mock_client.post.call_count == 3

    @patch("httpx.Client")
    def test_query_all_retries_failed(
        self, mock_client_class, basic_config, sample_schema
    ):
        """Test query when all retries fail."""
        # Setup mock client to always fail
        mock_client = Mock()
        mock_client.post.side_effect = httpx.ConnectError("Connection failed")
        mock_client_class.return_value = mock_client

        adapter = HTTPSUTAdapter(basic_config)
        adapter.retry_count = 2
        adapter.retry_delay = 0.01
        adapter.initialize()

        result = adapter.query("Test", sample_schema)

        assert result.success is False
        assert "failed after 2 attempts" in result.error
        assert mock_client.post.call_count == 2

    @patch("httpx.Client")
    def test_query_with_custom_response_mapping(
        self, mock_client_class, custom_mapping_config, sample_schema
    ):
        """Test query with custom response field mapping."""
        # Setup mock response with custom fields
        mock_response = Mock()
        mock_response.json.return_value = {
            "generated_query": "SELECT * FROM users",
            "results": [{"id": 1, "name": "Alice"}],
        }
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = HTTPSUTAdapter(custom_mapping_config)
        adapter.initialize()

        result = adapter.query("Get users", sample_schema)

        assert result.success is True
        assert result.generated_sql == "SELECT * FROM users"
        assert len(result.result_dataframe) == 1
        assert result.result_dataframe.iloc[0]["name"] == "Alice"

    @patch("httpx.Client")
    def test_query_with_token_usage(
        self, mock_client_class, basic_config, sample_schema
    ):
        """Test query response with token usage information."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "sql": "SELECT 1",
            "data": [],
            "tokens": {"input": 50, "output": 30, "total": 80},
        }
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = HTTPSUTAdapter(basic_config)
        adapter.initialize()

        result = adapter.query("Test", sample_schema)

        assert result.success is True
        assert result.token_available is True
        assert result.token_usage is not None
        assert result.token_usage.input_tokens == 50
        assert result.token_usage.output_tokens == 30
        assert result.token_usage.total_tokens == 80

    @patch("httpx.Client")
    def test_query_get_method(self, mock_client_class, sample_schema):
        """Test query using GET method."""
        config = SUTConfig(
            name="TestHTTPSUT",
            type="http",
            version="1.0.0",
            config={
                "api_url": "https://api.example.com/nl2sql",
                "method": "GET",
            },
        )

        mock_response = Mock()
        mock_response.json.return_value = {"sql": "SELECT 1", "data": []}
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = HTTPSUTAdapter(config)
        adapter.initialize()

        result = adapter.query("Test", sample_schema)

        assert result.success is True
        mock_client.get.assert_called_once()
        mock_client.post.assert_not_called()

    @patch("httpx.Client")
    def test_cleanup(self, mock_client_class, basic_config):
        """Test adapter cleanup."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        adapter = HTTPSUTAdapter(basic_config)
        adapter.initialize()

        assert adapter._initialized is True
        assert adapter._client is not None

        adapter.cleanup()

        assert adapter._initialized is False
        assert adapter._client is None
        mock_client.close.assert_called_once()

    def test_get_metadata(self, basic_config):
        """Test getting adapter metadata."""
        adapter = HTTPSUTAdapter(basic_config)
        metadata = adapter.get_metadata()

        assert metadata["name"] == "TestHTTPSUT"
        assert metadata["type"] == "http"
        assert metadata["api_url"] == "https://api.example.com/nl2sql"
        assert metadata["method"] == "POST"
        assert metadata["timeout"] == 30.0

    @patch("httpx.Client")
    def test_query_not_initialized(self, mock_client_class, basic_config, sample_schema):
        """Test query fails when adapter not initialized."""
        adapter = HTTPSUTAdapter(basic_config)

        with pytest.raises(SUTAdapterError, match="not initialized"):
            adapter.query("Test", sample_schema)

    @patch("httpx.Client")
    def test_parse_response_with_confidence(
        self, mock_client_class, basic_config, sample_schema
    ):
        """Test parsing response with confidence score."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "sql": "SELECT 1",
            "data": [],
            "confidence": 0.95,
            "model_version": "v2.1.0",
        }
        mock_response.raise_for_status = Mock()

        mock_client = Mock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        adapter = HTTPSUTAdapter(basic_config)
        adapter.initialize()

        result = adapter.query("Test", sample_schema)

        assert result.confidence == 0.95
        assert result.model_version == "v2.1.0"
