"""
Tests for Schema Generator module (onb/schemas/generator.py).

This module tests DDL generation for multiple database backends.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from onb.schemas.generator import SchemaGenerator


class TestSchemaGenerator:
    """Test SchemaGenerator class."""

    def test_initialization(self, tmp_path: Path):
        """Test generator initialization."""
        generator = SchemaGenerator(output_dir=str(tmp_path))

        assert generator.output_dir == tmp_path
        assert tmp_path.exists()

    def test_get_table_count(self):
        """Test getting table count."""
        generator = SchemaGenerator()
        count = generator.get_table_count()

        # Should have at least 36 tables from Phase 1
        assert count >= 36
        assert isinstance(count, int)

    def test_get_table_list(self):
        """Test getting table list."""
        generator = SchemaGenerator()
        tables = generator.get_table_list()

        # Should return sorted list of table names
        assert isinstance(tables, list)
        assert len(tables) >= 36
        assert all(isinstance(t, str) for t in tables)

        # Check some expected tables
        assert "ord_order_main" in tables
        assert "pay_payment_order" in tables
        assert "log_warehouse" in tables

        # Should be sorted
        assert tables == sorted(tables)

    def test_generate_ddl_postgresql(self):
        """Test PostgreSQL DDL generation."""
        generator = SchemaGenerator()
        ddl = generator.generate_ddl("postgresql", "ecommerce")

        assert isinstance(ddl, str)
        assert len(ddl) > 0

        # Check for PostgreSQL-specific syntax
        assert "CREATE TABLE" in ddl
        assert "BIGSERIAL" in ddl or "BIGINT" in ddl
        assert "-- PostgreSQL Schema" in ddl
        assert "SET client_encoding" in ddl
        assert "CREATE SCHEMA IF NOT EXISTS ecommerce" in ddl

    def test_generate_ddl_mysql(self):
        """Test MySQL DDL generation."""
        generator = SchemaGenerator()
        ddl = generator.generate_ddl("mysql", "ecommerce")

        assert isinstance(ddl, str)
        assert len(ddl) > 0

        # Check for MySQL-specific syntax
        assert "CREATE TABLE" in ddl
        assert "-- MySQL Schema" in ddl
        assert "SET NAMES utf8mb4" in ddl
        assert "CREATE DATABASE IF NOT EXISTS ecommerce" in ddl
        assert "USE ecommerce" in ddl

    def test_generate_ddl_doris(self):
        """Test Apache Doris DDL generation."""
        generator = SchemaGenerator()
        ddl = generator.generate_ddl("doris", "ecommerce")

        assert isinstance(ddl, str)
        assert len(ddl) > 0

        # Check for Doris syntax (MySQL-compatible)
        assert "CREATE TABLE" in ddl
        assert "-- Apache Doris Schema" in ddl
        assert "SET NAMES utf8mb4" in ddl

    @pytest.mark.skip(reason="ClickHouse SQLAlchemy dialect not installed")
    def test_generate_ddl_clickhouse(self):
        """Test ClickHouse DDL generation."""
        generator = SchemaGenerator()
        ddl = generator.generate_ddl("clickhouse", "ecommerce")

        assert isinstance(ddl, str)
        assert len(ddl) > 0

        # Check for ClickHouse syntax
        assert "CREATE TABLE" in ddl
        assert "-- ClickHouse Schema" in ddl

    def test_export_to_file_postgresql(self, tmp_path: Path):
        """Test exporting PostgreSQL DDL to file."""
        generator = SchemaGenerator(output_dir=str(tmp_path))
        output_path = generator.export_to_file("postgresql", "ecommerce")

        assert output_path.exists()
        assert output_path.parent == tmp_path / "postgresql"
        assert output_path.name == "ecommerce_schema.sql"

        # Check file contents
        content = output_path.read_text()
        assert "CREATE TABLE" in content
        assert "-- PostgreSQL Schema" in content

    def test_export_to_file_mysql(self, tmp_path: Path):
        """Test exporting MySQL DDL to file."""
        generator = SchemaGenerator(output_dir=str(tmp_path))
        output_path = generator.export_to_file("mysql", "ecommerce")

        assert output_path.exists()
        assert output_path.parent == tmp_path / "mysql"
        assert output_path.name == "ecommerce_schema.sql"

        content = output_path.read_text()
        assert "CREATE TABLE" in content
        assert "-- MySQL Schema" in content

    def test_export_to_file_custom_filename(self, tmp_path: Path):
        """Test exporting with custom filename."""
        generator = SchemaGenerator(output_dir=str(tmp_path))
        output_path = generator.export_to_file(
            "postgresql", "ecommerce", filename="custom.sql"
        )

        assert output_path.exists()
        assert output_path.name == "custom.sql"

    def test_export_all_databases(self, tmp_path: Path):
        """Test exporting all databases."""
        generator = SchemaGenerator(output_dir=str(tmp_path))
        results = generator.export_all_databases("ecommerce")

        # Should have results for all databases
        assert "postgresql" in results
        assert "mysql" in results
        assert "doris" in results
        assert "clickhouse" in results

        # PostgreSQL, MySQL, Doris should succeed
        assert results["postgresql"] is not None
        assert results["mysql"] is not None
        assert results["doris"] is not None

        # Check files exist
        assert results["postgresql"].exists()
        assert results["mysql"].exists()
        assert results["doris"].exists()

    def test_print_summary(self, capsys):
        """Test printing schema summary."""
        generator = SchemaGenerator()
        generator.print_summary()

        captured = capsys.readouterr()
        output = captured.out

        assert "Schema Summary" in output
        assert "Total tables:" in output
        assert "Tables:" in output
        # Check for some expected tables
        assert "ord_order_main" in output
        assert "pay_payment_order" in output

    @patch("onb.schemas.generator.create_engine")
    @patch("onb.schemas.generator.Base")
    def test_create_all_tables(self, mock_base: MagicMock, mock_engine: MagicMock):
        """Test creating all tables in database."""
        generator = SchemaGenerator()
        mock_engine_instance = MagicMock()
        mock_engine.return_value = mock_engine_instance

        generator.create_all_tables(
            "postgresql", "postgresql://user:pass@localhost:5432/testdb"
        )

        # Should have called create_engine and create_all
        mock_engine.assert_called_once()
        mock_base.metadata.create_all.assert_called_once_with(mock_engine_instance)


class TestSchemaGeneratorPreambles:
    """Test database-specific preambles and postambles."""

    def test_postgresql_preamble(self):
        """Test PostgreSQL preamble."""
        generator = SchemaGenerator()
        preamble = generator._get_database_preamble("postgresql", "ecommerce")

        assert isinstance(preamble, list)
        assert len(preamble) > 0
        # Join to check content
        text = "\n".join(preamble)
        assert "PostgreSQL" in text
        assert "SET client_encoding" in text
        assert "CREATE SCHEMA IF NOT EXISTS ecommerce" in text

    def test_mysql_preamble(self):
        """Test MySQL preamble."""
        generator = SchemaGenerator()
        preamble = generator._get_database_preamble("mysql", "ecommerce")

        assert isinstance(preamble, list)
        text = "\n".join(preamble)
        assert "MySQL" in text
        assert "SET NAMES utf8mb4" in text
        assert "SET FOREIGN_KEY_CHECKS = 0" in text

    def test_clickhouse_preamble(self):
        """Test ClickHouse preamble."""
        generator = SchemaGenerator()
        preamble = generator._get_database_preamble("clickhouse", "ecommerce")

        assert isinstance(preamble, list)
        text = "\n".join(preamble)
        assert "ClickHouse" in text

    def test_doris_preamble(self):
        """Test Apache Doris preamble."""
        generator = SchemaGenerator()
        preamble = generator._get_database_preamble("doris", "ecommerce")

        assert isinstance(preamble, list)
        text = "\n".join(preamble)
        assert "Doris" in text
        assert "SET FOREIGN_KEY_CHECKS = 0" in text

    def test_mysql_postamble(self):
        """Test MySQL postamble."""
        generator = SchemaGenerator()
        postamble = generator._get_database_postamble("mysql")

        assert isinstance(postamble, list)
        text = "\n".join(postamble)
        assert "SET FOREIGN_KEY_CHECKS = 1" in text

    def test_postgresql_postamble(self):
        """Test PostgreSQL postamble (should be empty or minimal)."""
        generator = SchemaGenerator()
        postamble = generator._get_database_postamble("postgresql")

        assert isinstance(postamble, list)


class TestSchemaGeneratorCLI:
    """Test CLI interface of schema generator."""

    @patch("onb.schemas.generator.SchemaGenerator")
    def test_cli_main_with_database(self, mock_generator_class: MagicMock):
        """Test CLI main function with specific database."""
        from onb.schemas.generator import main
        import sys

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        # Simulate command line arguments
        with patch.object(
            sys,
            "argv",
            ["generator.py", "--database", "postgresql", "--scenario", "ecommerce"],
        ):
            try:
                main()
            except SystemExit:
                pass

        # Should have called export_to_file
        mock_generator.export_to_file.assert_called_once_with("postgresql", "ecommerce")

    @patch("onb.schemas.generator.SchemaGenerator")
    def test_cli_main_with_all(self, mock_generator_class: MagicMock):
        """Test CLI main function with --all flag."""
        from onb.schemas.generator import main
        import sys

        mock_generator = MagicMock()
        mock_generator.export_all_databases.return_value = {
            "postgresql": Path("/tmp/postgresql.sql"),
            "mysql": Path("/tmp/mysql.sql"),
            "clickhouse": None,
            "doris": Path("/tmp/doris.sql"),
        }
        mock_generator_class.return_value = mock_generator

        with patch.object(sys, "argv", ["generator.py", "--all"]):
            try:
                main()
            except SystemExit:
                pass

        # Should have called export_all_databases
        mock_generator.export_all_databases.assert_called_once()

    @patch("onb.schemas.generator.SchemaGenerator")
    def test_cli_main_with_summary(self, mock_generator_class: MagicMock):
        """Test CLI main function with --summary flag."""
        from onb.schemas.generator import main
        import sys

        mock_generator = MagicMock()
        mock_generator_class.return_value = mock_generator

        with patch.object(sys, "argv", ["generator.py", "--summary"]):
            try:
                main()
            except SystemExit:
                pass

        # Should have called print_summary
        mock_generator.print_summary.assert_called_once()
