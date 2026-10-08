"""The ``orderby`` parameter, and the deterministic ordering pagination needs.

Two things live here because they are the same concern.

**``orderby``.** The contract documents it on all 13 collection paths as a csv
list of column names, where a ``-`` prefix means descending: *"Set the order of
the requested records, by prefixing '-' on the column name you can get records
by descending order. Comma separated list can also be provided."* The names are
**wire** names, so they need the same per-model translation as a filter, and
``filtering.FILTER_MAPS`` already holds exactly the right set — the scalar
columns. A nested wire object such as ``Job.Total`` is composed by
``serializers.py`` from several columns and is not one, so it cannot be ordered
on any more than it can be filtered on.

An unrecognised field raises :class:`UnknownOrderFieldError`, which ``main.py``
turns into a 400, matching what S6 did for an unknown filter. Accepting it and
returning unsorted rows would be the same lie: the caller cannot see from the
response that the parameter did nothing.

**The default order.** Before this module, ``paginate_query`` applied
``.offset().limit()`` to a query with no ``ORDER BY`` at all. PostgreSQL
guarantees no row order for an unordered query, so page boundaries were not
stable even in principle — a row could repeat on two pages or be skipped while
``iter_all()`` walked them. It never bit us because the seeded tables are small
and came back in insertion order, which is exactly the kind of accident that
stops being true under a different plan.

So every paginated query is ordered here, and ``id`` is always the final
tiebreak: ``orderby=Name`` over rows that share a name is otherwise just as
unstable as no ordering at all.
"""

from sqlalchemy.orm import Query

from simpro_mock.filtering import FILTER_MAPS

#: Prefixed to a column name to reverse it, per the contract's description.
DESC_PREFIX = "-"


class UnknownOrderFieldError(ValueError):
    """``orderby`` named a field this resource cannot be ordered by.

    Carries the offending name and the names that would have worked, so the
    400 can say both. ``main.py`` installs the handler.
    """

    def __init__(self, name: str, model: type, allowed: list[str]) -> None:
        self.name = name
        self.model_name = model.__name__
        self.allowed = allowed
        super().__init__(
            f"Unknown orderby field {name!r} for {self.model_name}. "
            f"Orderable fields: {', '.join(allowed)}."
        )


def orderable_fields(model: type) -> list[str]:
    """Return the wire names this model can be ordered by, sorted.

    The same set as the filterable fields, for the same reason: both need a
    real scalar column behind the wire name.
    """
    return sorted(FILTER_MAPS.get(model, {}))


def parse_orderby(orderby: str | None) -> list[tuple[str, bool]]:
    """Parse the csv ``orderby`` parameter.

    Args:
        orderby: The raw parameter value, or ``None`` when absent.

    Returns:
        One ``(wire_name, descending)`` pair per requested field, in the order
        given. An empty or whitespace-only value yields an empty list, so
        ``?orderby=`` behaves as if it had been omitted.
    """
    if not orderby:
        return []
    fields = []
    for raw in orderby.split(","):
        name = raw.strip()
        if not name:
            continue
        if name.startswith(DESC_PREFIX):
            fields.append((name[len(DESC_PREFIX) :].strip(), True))
        else:
            fields.append((name, False))
    return [(name, descending) for name, descending in fields if name]


def apply_ordering(query: Query, model: type, orderby: str | None) -> Query:
    """Order a query by the requested wire columns, then always by ``id``.

    Args:
        query: The query to order.
        model: The ORM class being queried; selects the name map.
        orderby: The raw ``orderby`` parameter, or ``None`` when absent.

    Returns:
        The query, ordered. With no ``orderby`` that is ``ORDER BY id``, which
        is what makes pagination deterministic.

    Raises:
        UnknownOrderFieldError: If a requested field is not a scalar column of
            ``model``.
    """
    field_map = FILTER_MAPS.get(model, {})
    criteria = []

    for wire_name, descending in parse_orderby(orderby):
        column_name = field_map.get(wire_name)
        column = getattr(model, column_name, None) if column_name else None
        if column is None:
            # Either the name is not in the map, or the map names a column the
            # model does not have, which would be a bug in FILTER_MAPS rather
            # than bad input. Fail loudly either way.
            raise UnknownOrderFieldError(wire_name, model, orderable_fields(model))
        criteria.append(column.desc() if descending else column.asc())

    # The tiebreak, unless the caller already ordered by the primary key.
    if not any(criterion.element is model.id for criterion in criteria):
        criteria.append(model.id.asc())

    return query.order_by(*criteria)
