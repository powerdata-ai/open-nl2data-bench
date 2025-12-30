"""
HTTP API SUT adapter for OpenNL2SQL-Bench.

This adapter allows testing NL2SQL systems through HTTP/REST APIs.
"""

import time
from typing import Any, Dict, Optional

import httpx
import pandas as pd

from onb.adapters.sut.base import SUTAdapter
from onb.core.exceptions import SUTAdapterError
from onb.core.types import (
    NL2SQLResponse,
    SchemaInfo,
    SUTConfig,
    TimingBreakdown,
    TokenUsage,
)


class HTTPSUTAdapter(SUTAdapter):
    """
    HTTP API adapter for NL2SQL systems.

    Supports flexible configuration for various API formats and authentication methods.

    Configuration example:
        {
            "api_url": "https://api.example.com/nl2sql",
            "method": "POST",
            "auth_type": "bearer",  # or "api_key", "basic", "none"
            "auth_token": "your-token",
            "headers": {"X-Custom": "value"},
            "timeout": 30,
            "retry_count": 3,
            "retry_delay": 1.0,
            "request_mapping": {
                "question_key": "query",
                "schema_key": "database_schema",
                "language_key": "lang"
            },
            "response_mapping": {
                "sql_key": "generated_sql",
                "data_key": "result_data",
                "error_key": "error_message",
                "time_key": "execution_time_ms"
            }
        }
    """

    def __init__(self, config: SUTConfig):
        """
        Initialize HTTP SUT adapter.

        Args:
            config: SUT configuration with HTTP API settings
        """
        super().__init__(config)

        # API endpoint configuration
        self.api_url = config.config.get("api_url")
        self.method = config.config.get("method", "POST").upper()
        self.timeout = config.config.get("timeout", 30.0)

        # Authentication configuration
        self.auth_type = config.config.get("auth_type", "none")
        self.auth_token = config.config.get("auth_token")
        self.api_key = config.config.get("api_key")
        self.username = config.config.get("username")
        self.password = config.config.get("password")

        # Custom headers
        self.custom_headers = config.config.get("headers", {})

        # Retry configuration
        self.retry_count = config.config.get("retry_count", 3)
        self.retry_delay = config.config.get("retry_delay", 1.0)

        # Request/Response mapping
        self.request_mapping = config.config.get("request_mapping", {})
        self.response_mapping = config.config.get("response_mapping", {})

        # HTTP client
        self._client: Optional[httpx.Client] = None

    def initialize(self) -> None:
        """Initialize the HTTP client."""
        if not self.api_url:
            raise SUTAdapterError("api_url is required in configuration")

        # Build headers
        headers = self._build_headers()

        # Build auth
        auth = self._build_auth()

        # Create HTTP client
        self._client = httpx.Client(
            headers=headers,
            auth=auth,
            timeout=self.timeout,
            follow_redirects=True,
        )

        self._initialized = True

    def query(
        self,
        question: str,
        schema: SchemaInfo,
        language: str = "zh",
        **kwargs: Any,
    ) -> NL2SQLResponse:
        """
        Execute NL2SQL query via HTTP API.

        Args:
            question: Natural language question
            schema: Database schema information
            language: Question language
            **kwargs: Additional parameters

        Returns:
            NL2SQLResponse with API results
        """
        if not self._initialized or not self._client:
            raise SUTAdapterError("Adapter not initialized")

        start_time = time.time()

        # Build request payload
        payload = self._build_request_payload(question, schema, language, kwargs)

        # Execute request with retry
        for attempt in range(self.retry_count):
            try:
                response_data, request_time = self._execute_request(payload)

                # Parse response
                return self._parse_response(
                    response_data,
                    start_time,
                    request_time,
                )

            except httpx.HTTPError as e:
                if attempt < self.retry_count - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    return NL2SQLResponse(
                        generated_sql="",
                        success=False,
                        error=f"HTTP request failed after {self.retry_count} attempts: {e}",
                        total_time_ms=(time.time() - start_time) * 1000,
                    )

            except Exception as e:
                return NL2SQLResponse(
                    generated_sql="",
                    success=False,
                    error=f"Unexpected error: {e}",
                    total_time_ms=(time.time() - start_time) * 1000,
                )

        # Should not reach here
        return NL2SQLResponse(
            generated_sql="",
            success=False,
            error="Max retries exceeded",
            total_time_ms=(time.time() - start_time) * 1000,
        )

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers with authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Add authentication headers
        if self.auth_type == "bearer" and self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.auth_type == "api_key" and self.api_key:
            headers["X-API-Key"] = self.api_key

        # Add custom headers
        headers.update(self.custom_headers)

        return headers

    def _build_auth(self) -> Optional[httpx.Auth]:
        """Build authentication for httpx client."""
        if self.auth_type == "basic" and self.username and self.password:
            return httpx.BasicAuth(self.username, self.password)
        return None

    def _build_request_payload(
        self,
        question: str,
        schema: SchemaInfo,
        language: str,
        extra: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build request payload with custom field mapping.

        Args:
            question: Natural language question
            schema: Database schema
            language: Question language
            extra: Extra parameters

        Returns:
            Request payload dictionary
        """
        # Default field names
        question_key = self.request_mapping.get("question_key", "question")
        schema_key = self.request_mapping.get("schema_key", "schema")
        language_key = self.request_mapping.get("language_key", "language")

        # Build payload
        payload = {
            question_key: question,
            schema_key: schema.to_dict(),
            language_key: language,
        }

        # Add extra parameters
        for key, value in extra.items():
            if key not in payload:
                payload[key] = value

        return payload

    def _execute_request(
        self, payload: Dict[str, Any]
    ) -> tuple[Dict[str, Any], float]:
        """
        Execute HTTP request and measure time.

        Args:
            payload: Request payload

        Returns:
            Tuple of (response_data, request_time_ms)
        """
        request_start = time.time()

        if self.method == "POST":
            response = self._client.post(self.api_url, json=payload)
        elif self.method == "GET":
            response = self._client.get(self.api_url, params=payload)
        else:
            raise SUTAdapterError(f"Unsupported HTTP method: {self.method}")

        request_time = (time.time() - request_start) * 1000

        response.raise_for_status()
        response_data = response.json()

        return response_data, request_time

    def _parse_response(
        self,
        response_data: Dict[str, Any],
        start_time: float,
        request_time: float,
    ) -> NL2SQLResponse:
        """
        Parse API response into NL2SQLResponse.

        Args:
            response_data: Response from API
            start_time: Request start timestamp
            request_time: HTTP request time in ms

        Returns:
            NL2SQLResponse object
        """
        # Default field names
        sql_key = self.response_mapping.get("sql_key", "sql")
        data_key = self.response_mapping.get("data_key", "data")
        error_key = self.response_mapping.get("error_key", "error")
        time_key = self.response_mapping.get("time_key", "time_ms")
        token_key = self.response_mapping.get("token_key", "tokens")

        # Extract fields
        generated_sql = response_data.get(sql_key, "")
        error_message = response_data.get(error_key)
        execution_time = response_data.get(time_key, request_time)

        # Check for error
        if error_message:
            return NL2SQLResponse(
                generated_sql=generated_sql,
                success=False,
                error=error_message,
                total_time_ms=(time.time() - start_time) * 1000,
            )

        # Parse result data
        result_df = None
        result_data = response_data.get(data_key)
        if result_data:
            try:
                if isinstance(result_data, list):
                    result_df = pd.DataFrame(result_data)
                elif isinstance(result_data, dict):
                    result_df = pd.DataFrame([result_data])
            except Exception as e:
                return NL2SQLResponse(
                    generated_sql=generated_sql,
                    success=False,
                    error=f"Failed to parse result data: {e}",
                    total_time_ms=(time.time() - start_time) * 1000,
                )

        # Parse token usage
        token_usage = None
        token_data = response_data.get(token_key)
        if token_data:
            token_usage = TokenUsage(
                input_tokens=token_data.get("input", 0),
                output_tokens=token_data.get("output", 0),
                total_tokens=token_data.get("total", 0),
            )

        # Build timing breakdown
        total_time = (time.time() - start_time) * 1000
        timing_breakdown = TimingBreakdown(
            nl2sql_time_ms=execution_time,
            sql_generation_time_ms=execution_time * 0.7,  # Estimate
            sql_execution_time_ms=execution_time * 0.3,  # Estimate
            total_time_ms=total_time,
        )

        return NL2SQLResponse(
            generated_sql=generated_sql,
            result_dataframe=result_df,
            success=True,
            total_time_ms=total_time,
            timing_breakdown=timing_breakdown,
            timing_source="sut",
            token_usage=token_usage,
            token_available=token_usage is not None,
            confidence=response_data.get("confidence"),
            model_version=response_data.get("model_version"),
        )

    def cleanup(self) -> None:
        """Clean up HTTP client resources."""
        if self._client:
            self._client.close()
            self._client = None
        self._initialized = False

    def get_metadata(self) -> Dict[str, Any]:
        """Get HTTP adapter metadata."""
        metadata = super().get_metadata()
        metadata.update({
            "api_url": self.api_url,
            "method": self.method,
            "auth_type": self.auth_type,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
        })
        return metadata
