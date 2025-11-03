import json
import pytest
import os
from db_context import DatabaseContext
from db_context.schema.formatter import format_sql_query_result, format_as_json, MAX_CELL_WIDTH

pytestmark = pytest.mark.asyncio

async def test_max_rows_and_truncation(db_context_read_only: DatabaseContext):
    # Generate a long string exceeding MAX_CELL_WIDTH
    long_literal = 'X' * (MAX_CELL_WIDTH + 50)
    sql = f"SELECT '{long_literal}' AS LONGCOL FROM dual"
    result = await db_context_read_only.run_sql_query(sql, max_rows=1)
    table_md = format_sql_query_result(result)
    assert 'LONGCOL' in table_md
    # Ensure truncated (ellipsis)
    assert '…' in table_md
    assert len(table_md.split('\n')[2]) < MAX_CELL_WIDTH + 20  # padded row line
    assert 'Note: Some values truncated' in table_md

async def test_escape_pipes_and_backticks(db_context_read_only: DatabaseContext):
    sql = "SELECT 'a|b`c' AS COL FROM dual"
    result = await db_context_read_only.run_sql_query(sql)
    md = format_sql_query_result(result)
    # Escaped pipe
    assert 'a\\|b' in md
    # Backticks replaced
    assert '`' not in md


async def test_json_output_format(db_context_read_only: DatabaseContext):
    """Test that JSON output format works correctly with actual database queries."""
    sql = "SELECT 1 AS ID, 'TEST' AS NAME FROM dual"
    result = await db_context_read_only.run_sql_query(sql)
    
    json_output = format_sql_query_result(result, output_format="json")
    parsed = json.loads(json_output)
    
    assert parsed["row_count"] == 1
    assert "ID" in parsed["columns"]
    assert "NAME" in parsed["columns"]
    assert len(parsed["rows"]) == 1
    assert parsed["rows"][0]["ID"] == 1
    assert parsed["rows"][0]["NAME"] == "TEST"


async def test_json_output_format_empty_result(db_context_read_only: DatabaseContext):
    """Test JSON output for empty query results."""
    sql = "SELECT * FROM dual WHERE 1=0"
    result = await db_context_read_only.run_sql_query(sql)
    
    json_output = format_sql_query_result(result, output_format="json")
    parsed = json.loads(json_output)
    
    assert parsed["row_count"] == 0
    assert "message" in parsed
    assert "returned no rows" in parsed["message"]
