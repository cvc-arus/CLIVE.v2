"""Simpro-style query parameter filtering with operator support."""

import re
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

# Query params that control pagination, not filtering
PAGINATION_PARAMS = {"page", "pagesize", "columns", "orderby", "search", "limit"}

# Regex to match Simpro operator expressions like gt(100) or between(5,10)
OPERATOR_PATTERN = re.compile(r"^(gt|lt|le|ge|ne|between|in|!in)\((.+)\)$")

# Map PascalCase query param names to snake_case model column names
PASCAL_TO_SNAKE = {
    "ID": "id",
    "Name": "name",
    "CompanyID": "company_id",
    "GivenName": "given_name",
    "FamilyName": "family_name",
    "Email": "email",
    "Phone": "phone",
    "Status": "status",
    "DateIssued": "date_issued",
    "Total": "total",
    "CustomerID": "customer_id",
}


def parse_operator(value: str) -> tuple[str, Any]:
    """Parse a Simpro operator expression. Returns (operator, parsed_value)."""
    match = OPERATOR_PATTERN.match(value)
    if not match:
        # No operator syntax found, treat as exact match
        return "eq", value

    op = match.group(1)
    raw = match.group(2)

    # between() and in() operators contain comma-separated values
    if op == "between":
        parts = [p.strip() for p in raw.split(",")]
        return op, parts
    if op in ("in", "!in"):
        parts = [p.strip() for p in raw.split(",")]
        return op, parts

    return op, raw


def build_filter_expression(column, operator: str, value: Any):
    """Convert an operator and value into a SQLAlchemy filter expression."""
    if operator == "eq":
        return column == value
    if operator == "gt":
        return column > _cast_numeric(value)
    if operator == "lt":
        return column < _cast_numeric(value)
    if operator == "ge":
        return column >= _cast_numeric(value)
    if operator == "le":
        return column <= _cast_numeric(value)
    if operator == "ne":
        return column != value
    if operator == "between":
        return column.between(_cast_numeric(value[0]), _cast_numeric(value[1]))
    if operator == "in":
        return column.in_(value)
    if operator == "!in":
        return ~column.in_(value)
    return column == value


def _cast_numeric(value: str):
    """Try to cast a string to int or float for comparison operators."""
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def apply_filters(query: Query, model, query_params: dict[str, str]) -> Query:
    """Apply Simpro-style filters from query parameters to a SQLAlchemy query."""
    # Default to AND mode if search param is not specified
    search_mode = query_params.get("search", "all").lower()
    filters = []

    for param_name, param_value in query_params.items():
        # Skip pagination-related params
        if param_name.lower() in PAGINATION_PARAMS:
            continue

        # Map PascalCase param name to snake_case column name
        column_name = PASCAL_TO_SNAKE.get(param_name)
        if column_name is None:
            continue

        column = getattr(model, column_name, None)
        if column is None:
            continue

        # Parse any operator syntax and build the filter
        operator, parsed_value = parse_operator(param_value)
        filter_expr = build_filter_expression(column, operator, parsed_value)
        filters.append(filter_expr)

    if not filters:
        return query

    # Combine filters with AND (search=all) or OR (search=any)
    if search_mode == "any":
        return query.filter(or_(*filters))
    return query.filter(and_(*filters))
