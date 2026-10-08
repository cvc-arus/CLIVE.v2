"""Live smoke tests against a running simpro-mock service."""

import httpx
import pytest

BASE = "http://localhost:8100"
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module", autouse=True)
def require_mock() -> None:
    """Skip at test runtime, never while pytest imports or collects the module."""
    try:
        response = httpx.get(f"{BASE}/health", timeout=1.0)
        response.raise_for_status()
    except httpx.HTTPError:
        pytest.skip(
            "simpro-mock is not running on localhost:8100 "
            "(start it with: docker compose up -d simpro-mock)"
        )


@pytest.fixture(scope="module")
def token() -> str:
    response = httpx.post(
        f"{BASE}/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": "test",
            "client_secret": "test",
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_companies_list_uses_pascal_case_and_pagination_headers(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = httpx.get(f"{BASE}/api/v1.0/companies/", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data
    assert "ID" in data[0]
    assert "Result-Total" in response.headers
    assert "Result-Pages" in response.headers
    assert "Result-Count" in response.headers


def test_unauthenticated_request_returns_401():
    response = httpx.get(f"{BASE}/api/v1.0/companies/")
    assert response.status_code == 401


def test_customer_subtype_routes_are_type_scoped(token: str):
    """A subtype detail route 404s when the id names the other kind.

    The polymorphic ``/customers/`` list hands callers a ``Type`` and an
    ``_href``; following the wrong one must fail loudly rather than return a
    record of the wrong shape (ADR-013 decision 2).
    """
    headers = {"Authorization": f"Bearer {token}"}
    summaries = httpx.get(
        f"{BASE}/api/v1.0/companies/1/customers/", headers=headers
    ).json()

    by_type = {}
    for row in summaries:
        by_type.setdefault(row["Type"], row)
    assert set(by_type) == {"Individual", "Company"}, (
        f"the seed must provide both customer kinds, got {sorted(by_type)}"
    )

    # Each id resolves on its own subtype route...
    for kind, subtype in (("Individual", "individuals"), ("Company", "companies")):
        own = httpx.get(
            f"{BASE}/api/v1.0/companies/1/customers/{subtype}/{by_type[kind]['ID']}",
            headers=headers,
        )
        assert own.status_code == 200, f"{kind} should resolve under {subtype}"
        assert own.json()["Type"] == kind

    # ...and 404s on the other one.
    for kind, other in (("Individual", "companies"), ("Company", "individuals")):
        crossed = httpx.get(
            f"{BASE}/api/v1.0/companies/1/customers/{other}/{by_type[kind]['ID']}",
            headers=headers,
        )
        assert crossed.status_code == 404, (
            f"a {kind} id must not resolve under /{other}/, "
            f"got {crossed.status_code}"
        )


def test_customer_summary_href_points_at_a_fetchable_route(token: str):
    """Following a summary's ``_href`` returns that customer's full record.

    This is the only documented way to get from the list to the detail, since
    Simpro publishes no ``/customers/{id}``.
    """
    headers = {"Authorization": f"Bearer {token}"}
    summary = httpx.get(
        f"{BASE}/api/v1.0/companies/1/customers/?pageSize=1", headers=headers
    ).json()[0]

    detail = httpx.get(f"{BASE}{summary['_href']}", headers=headers)

    assert detail.status_code == 200, f"_href {summary['_href']} did not resolve"
    assert detail.json()["ID"] == summary["ID"]


def test_a_project_is_a_job_with_type_project(token: str):
    """Projects are jobs, not a resource of their own.

    Simpro publishes no Projects route; upstream a project is a job whose
    ``Type`` is ``"Project"`` (ADR-013 Wave C). So the mock must serve them
    through ``/jobs/`` and must not answer ``/projects/``.
    """
    headers = {"Authorization": f"Bearer {token}"}

    assert (
        httpx.get(f"{BASE}/api/v1.0/companies/1/projects/", headers=headers).status_code
        == 404
    ), "the mock still serves a Projects route"

    jobs = httpx.get(
        f"{BASE}/api/v1.0/companies/1/jobs/?pageSize=250", headers=headers
    ).json()
    assert jobs, "the mock seeded no jobs"

    types = set()
    for row in jobs:
        detail = httpx.get(
            f"{BASE}/api/v1.0/companies/1/jobs/{row['ID']}", headers=headers
        ).json()
        types.add(detail["Type"])
    assert "Project" in types, f"no Type=Project jobs are seeded, only {sorted(types)}"
    assert types <= {"Project", "Service", "Prepaid"}, f"undocumented Type in {types}"


def test_job_total_is_a_nested_object_with_two_decimal_money(token: str):
    """``Total`` is an object, and its members are exact to two places.

    The old mock returned a bare float. Both the narrow list projection and
    the detail route carry the three-way split (ADR-013).
    """
    headers = {"Authorization": f"Bearer {token}"}
    listed = httpx.get(
        f"{BASE}/api/v1.0/companies/1/jobs/?pageSize=1", headers=headers
    ).json()[0]

    assert set(listed) == {"ID", "Description", "Total"}, (
        f"the job list projection should be exactly ID, Description and Total, "
        f"got {sorted(listed)}"
    )
    assert set(listed["Total"]) == {"ExTax", "Tax", "IncTax"}

    for key, value in listed["Total"].items():
        assert isinstance(value, int | float), f"{key} is not a JSON number"
        assert round(float(value), 2) == float(value), (
            f"{key}={value} has more than two decimal places"
        )


def test_columns_narrows_a_collection_and_keeps_pagination_headers(token: str):
    """``columns`` projects the body without disturbing the headers.

    A projected response is returned as its own ``JSONResponse``, which
    discards headers set on the injected ``Response``, so this is the test
    that catches the pagination headers going missing (ADR-013 S6).
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE}/api/v1.0/companies/1/jobs/?pageSize=2&columns=Description"

    response = httpx.get(url, headers=headers)

    assert response.status_code == 200
    rows = response.json()
    assert rows, "the mock returned an empty first page"
    for row in rows:
        # ID is always included, even though only Description was asked for.
        assert set(row) == {"ID", "Description"}, f"unexpected keys {sorted(row)}"

    assert response.headers["Result-Count"] == str(len(rows))
    assert int(response.headers["Result-Total"]) >= len(rows)
    assert int(response.headers["Result-Pages"]) >= 1


def test_columns_selects_whole_nested_blocks_on_a_detail_route(token: str):
    """``columns`` picks top-level keys, and a key brings its whole object.

    The contract documents ``columns`` on detail routes as well as
    collections, and a selected key yields its entire nested block rather
    than a partial traversal.
    """
    headers = {"Authorization": f"Bearer {token}"}

    full = httpx.get(f"{BASE}/api/v1.0/companies/1/jobs/1", headers=headers).json()
    projected = httpx.get(
        f"{BASE}/api/v1.0/companies/1/jobs/1?columns=Name,Status", headers=headers
    ).json()

    assert set(projected) == {"ID", "Name", "Status"}
    # The nested Status object arrives intact, not flattened or truncated.
    assert projected["Status"] == full["Status"]
    assert set(projected["Status"]) == {"ID", "Name", "Color"}
    assert len(full) > len(projected), "the unprojected record should be wider"


def test_omitting_columns_returns_the_whole_record(token: str):
    """No ``columns`` means no projection, and an empty value is not one either."""
    headers = {"Authorization": f"Bearer {token}"}

    full = httpx.get(f"{BASE}/api/v1.0/companies/1/jobs/1", headers=headers).json()
    empty_param = httpx.get(
        f"{BASE}/api/v1.0/companies/1/jobs/1?columns=", headers=headers
    ).json()

    assert empty_param == full, "?columns= should behave as if omitted"


def test_an_unknown_filter_is_rejected_loudly(token: str):
    """An unmapped filter parameter returns 400 naming what would work.

    It used to be ignored, so the caller got unfiltered data and believed it
    was filtered. ``Status`` is the sharp case: jobs had a ``status`` text
    column before ADR-013 and now have a ``Status`` *object* composed from a
    foreign key, so the old filter name is no longer a column.
    """
    headers = {"Authorization": f"Bearer {token}"}

    response = httpx.get(
        f"{BASE}/api/v1.0/companies/1/jobs/?Status=Open", headers=headers
    )

    assert response.status_code == 400, (
        f"expected 400 for an unknown filter, got {response.status_code}"
    )
    body = response.json()
    assert body["parameter"] == "Status"
    assert body["resource"] == "Job"
    assert "Stage" in body["filterable"], (
        f"the error should name the usable fields, got {body['filterable']}"
    )


def test_a_known_filter_actually_narrows_the_result(token: str):
    """A mapped filter changes the result, rather than being accepted and ignored."""
    headers = {"Authorization": f"Bearer {token}"}
    base = f"{BASE}/api/v1.0/companies/1/jobs/?pageSize=250"

    everything = httpx.get(base, headers=headers)
    projects = httpx.get(f"{base}&Type=Project", headers=headers)

    assert projects.status_code == 200
    assert projects.json(), "Type=Project matched nothing; the seed should have some"
    assert int(projects.headers["Result-Total"]) < int(
        everything.headers["Result-Total"]
    ), "the filter did not narrow anything, so it is being ignored"


def test_request_control_parameters_are_not_treated_as_filters(token: str):
    """page, pageSize, columns, orderby, search and limit must not 400.

    They control the request rather than filtering it, so the loud-filter
    check has to skip them.
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = (
        f"{BASE}/api/v1.0/companies/1/jobs/"
        "?page=1&pageSize=5&columns=ID&orderby=Name&search=all&limit=5"
    )

    response = httpx.get(url, headers=headers)

    assert response.status_code == 200, (
        f"a request-control parameter was mistaken for a filter: {response.text}"
    )


def test_orderby_sorts_ascending_and_descending(token: str):
    """``orderby=Name`` sorts, and the ``-`` prefix reverses it.

    Before this, ``orderby`` sat in ``PAGINATION_PARAMS`` and was accepted and
    ignored, so a caller got arbitrary order and a 200 either way.
    """
    headers = {"Authorization": f"Bearer {token}"}
    base = f"{BASE}/api/v1.0/companies/1/employees/?pageSize=250&columns=ID,Name"

    ascending = httpx.get(f"{base}&orderby=Name", headers=headers)
    descending = httpx.get(f"{base}&orderby=-Name", headers=headers)

    assert ascending.status_code == 200
    assert descending.status_code == 200
    up = [row["Name"] for row in ascending.json()]
    down = [row["Name"] for row in descending.json()]

    assert len(up) > 1, "need at least two employees to tell sorted from unsorted"
    assert up == sorted(up), f"orderby=Name did not sort: {up}"
    assert down == list(reversed(up)), f"orderby=-Name did not reverse: {down}"


def test_orderby_accepts_a_csv_list_and_a_column_not_in_the_response(token: str):
    """A comma-separated list orders by each field in turn.

    ``Stage`` is deliberately chosen: the job *list* projection is only
    ``ID``, ``Description`` and ``Total``, so this also pins that a caller can
    order by a column the response does not contain, which is what real
    Simpro does.
    """
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{BASE}/api/v1.0/companies/1/jobs/?pageSize=250&columns=ID&orderby=Stage,-ID"

    response = httpx.get(url, headers=headers)

    assert response.status_code == 200, response.text
    ids = [row["ID"] for row in response.json()]
    assert len(ids) > 1
    assert ids != sorted(ids), (
        f"orderby=Stage,-ID left the rows in plain id order, so it was ignored: {ids}"
    )


def test_an_unknown_orderby_field_is_rejected_loudly(token: str):
    """An unorderable field returns 400 naming the fields that would work.

    Same contract as an unknown filter: a 200 with unsorted rows gives the
    caller no way to tell the parameter did nothing.
    """
    headers = {"Authorization": f"Bearer {token}"}

    response = httpx.get(
        f"{BASE}/api/v1.0/companies/1/jobs/?orderby=Total", headers=headers
    )

    assert response.status_code == 400, (
        f"expected 400 for an unorderable field, got {response.status_code}"
    )
    body = response.json()
    assert body["field"] == "Total"
    assert body["resource"] == "Job"
    assert "Stage" in body["orderable"], (
        f"the error should name the usable fields, got {body['orderable']}"
    )


def test_collection_pagination_visits_every_row_exactly_once(token: str):
    """Walking the pages must not repeat or skip a row.

    ``paginate_query`` used to apply ``.offset().limit()`` to a query with no
    ``ORDER BY``, which PostgreSQL gives no row order for, so stable page
    boundaries were an accident of table size rather than a property. Every
    paginated query is now ordered by ``id``.
    """
    headers = {"Authorization": f"Bearer {token}"}
    base = f"{BASE}/api/v1.0/companies/1/jobs/"

    first = httpx.get(f"{base}?pageSize=250&columns=ID", headers=headers)
    assert first.status_code == 200
    total = int(first.headers["Result-Total"])
    assert total > 2, "need several rows for paging to mean anything"

    page_size = 2
    walked: list[int] = []
    for page in range(1, (total // page_size) + 3):
        response = httpx.get(
            f"{base}?pageSize={page_size}&page={page}&columns=ID", headers=headers
        )
        assert response.status_code == 200
        rows = response.json()
        if not rows:
            break
        walked.extend(row["ID"] for row in rows)

    assert len(walked) == total, (
        f"walked {len(walked)} rows over the pages but Result-Total is {total}"
    )
    assert len(set(walked)) == total, f"a row appeared on more than one page: {walked}"


def test_limit_caps_the_records_returned(token: str):
    """``limit`` narrows the page and is reflected in the headers.

    ``Result-Total`` is the full filtered count and must not shrink; only the
    rows returned and ``Result-Pages`` follow the limit.
    """
    headers = {"Authorization": f"Bearer {token}"}
    base = f"{BASE}/api/v1.0/companies/1/jobs/?columns=ID"

    unlimited = httpx.get(f"{base}&pageSize=250", headers=headers)
    limited = httpx.get(f"{base}&pageSize=250&limit=2", headers=headers)

    assert limited.status_code == 200
    total = int(unlimited.headers["Result-Total"])
    assert total > 2, "need more rows than the limit for this to prove anything"

    assert len(limited.json()) == 2, (
        f"limit=2 returned {len(limited.json())} rows, so it was ignored"
    )
    assert int(limited.headers["Result-Count"]) == 2
    assert int(limited.headers["Result-Total"]) == total, (
        "limit must not change the reported total"
    )
    assert int(limited.headers["Result-Pages"]) > 1, (
        "Result-Pages should be recomputed from the effective page size"
    )


def test_limit_below_one_is_rejected(token: str):
    """``limit=0`` is a bad request, not an empty page.

    Matches how the ``pageSize`` bounds behave: FastAPI validates it before
    the handler runs.
    """
    headers = {"Authorization": f"Bearer {token}"}

    response = httpx.get(f"{BASE}/api/v1.0/companies/1/jobs/?limit=0", headers=headers)

    assert response.status_code == 422, (
        f"expected 422 for limit=0, got {response.status_code}"
    )
