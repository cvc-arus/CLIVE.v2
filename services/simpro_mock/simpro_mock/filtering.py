"""Simpro-style query parameter filtering with operator support.

Filter parameters are PascalCase wire names and have to be translated to ORM
column names. That mapping is **per model**: ``Name`` means
``companies.name`` on one route and nothing at all on another, and after the
ADR-013 re-shape most resources no longer have the fields the old single
shared map assumed.

An unrecognised filter parameter raises :class:`UnknownFilterParameterError`, which
``main.py`` turns into a 400. It used to be ignored silently, which meant a
renamed field left every test green while the filter quietly did nothing — the
caller got unfiltered data believing it was filtered.
"""

import re
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.orm import Query

from simpro_mock.models import (
    Asset,
    Attachment,
    Company,
    Contact,
    Customer,
    Employee,
    Job,
    JobNote,
    Quote,
    Site,
    Status,
)

# Query params that control the request, not the filter set.
PAGINATION_PARAMS = {"page", "pagesize", "columns", "orderby", "search", "limit"}

# Regex to match Simpro operator expressions like gt(100) or between(5,10)
OPERATOR_PATTERN = re.compile(r"^(gt|lt|le|ge|ne|between|in|!in)\((.+)\)$")

#: Wire name -> column name, per model. Only scalar columns appear: a nested
#: wire object such as ``Job.Total`` or ``Job.Status`` is composed by
#: ``serializers.py`` and is not a column, so it cannot be filtered on without
#: inventing behaviour Simpro may not have.
#:
#: Keys are the **wire** names from
#: ``docs/contracts/simpro-openapi-v1-get-subset.json``, not the column names.
FILTER_MAPS: dict[type, dict[str, str]] = {
    Company: {
        "ID": "id",
        "Name": "name",
    },
    Customer: {
        "ID": "id",
        "Type": "type",
        "CompanyName": "company_name",
        "GivenName": "given_name",
        "FamilyName": "family_name",
        "Email": "email",
        "Phone": "phone",
        "CustomerType": "customer_type",
        "Archived": "archived",
    },
    Contact: {
        "ID": "id",
        "GivenName": "given_name",
        "FamilyName": "family_name",
        "Email": "email",
        "Position": "position",
        "Department": "department",
    },
    Site: {
        "ID": "id",
        "Name": "name",
        "Archived": "archived",
    },
    Asset: {
        "ID": "id",
        "StartDate": "start_date",
        "DisplayOrder": "display_order",
        "Archived": "archived",
    },
    Employee: {
        "ID": "id",
        "Name": "name",
        "Position": "position",
        "Archived": "archived",
    },
    Job: {
        "ID": "id",
        "Name": "name",
        "Description": "description",
        "Type": "type",
        "Stage": "stage",
        "OrderNo": "order_no",
        "RequestNo": "request_no",
        "DateIssued": "date_issued",
    },
    Quote: {
        "ID": "id",
        "Name": "name",
        "Description": "description",
        "Type": "type",
        "Stage": "stage",
        "DateIssued": "date_issued",
        "IsClosed": "is_closed",
    },
    JobNote: {
        "ID": "id",
        "Subject": "subject",
    },
    Attachment: {
        "ID": "id",
        "Filename": "filename",
        "MimeType": "mime_type",
        "Public": "public",
    },
    Status: {
        "ID": "id",
        "Name": "name",
        "Priority": "priority",
    },
}


class UnknownFilterParameterError(ValueError):
    """A query parameter is neither a known filter nor a request control.

    Carries the offending name and the names that would have worked, so the
    400 response can say both. ``main.py`` installs the handler.
    """

    def __init__(self, name: str, model: type, allowed: list[str]) -> None:
        self.name = name
        self.model_name = model.__name__
        self.allowed = allowed
        super().__init__(
            f"Unknown filter parameter {name!r} for {self.model_name}. "
            f"Filterable fields: {', '.join(allowed)}."
        )


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


def filterable_fields(model: type) -> list[str]:
    """Return the wire names this model can be filtered on, sorted."""
    return sorted(FILTER_MAPS.get(model, {}))


def apply_filters(query: Query, model, query_params: dict[str, str]) -> Query:
    """Apply Simpro-style filters from query parameters to a SQLAlchemy query.

    Args:
        query: The query to narrow.
        model: The ORM class being queried; selects the filter map.
        query_params: The raw request query parameters.

    Returns:
        The query, narrowed by every filter parameter present.

    Raises:
        UnknownFilterParameterError: If a parameter is neither a request control
            (``page``, ``pageSize``, ``columns``, ``orderby``, ``search``,
            ``limit``) nor a filterable field of ``model``.
    """
    # Default to AND mode if search param is not specified
    search_mode = query_params.get("search", "all").lower()
    field_map = FILTER_MAPS.get(model, {})
    filters = []

    for param_name, param_value in query_params.items():
        # Skip the parameters that control the request rather than filter it
        if param_name.lower() in PAGINATION_PARAMS:
            continue

        column_name = field_map.get(param_name)
        if column_name is None:
            raise UnknownFilterParameterError(
                param_name, model, filterable_fields(model)
            )

        column = getattr(model, column_name, None)
        if column is None:
            # The map names a column the model does not have, which is a bug
            # in FILTER_MAPS rather than bad input. Fail loudly either way.
            raise UnknownFilterParameterError(
                param_name, model, filterable_fields(model)
            )

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
