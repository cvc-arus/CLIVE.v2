"""Opt-in, read-only contract tests against live Simpro (course correction W1 T3).

Skipped unless ``SIMPRO_LIVE_TESTS=1``. When enabled they read the live
settings from the environment and ``.env`` (the one exception to
``tests/CLAUDE.md`` §3), and talk to CVC's own build, which holds real data,
so:

* **GET only.** Every API request goes through the client's GET methods, and
  a request hook fails the test on any other method. The token request is
  the only POST, and it goes through ``AuthManager``'s own HTTP client.
* **No client data in output** (root ``CLAUDE.md`` §9). Assertions report
  status codes, counts, field names, header names and validation error
  locations, never values. ``simpro_client`` logging is disabled, so the build
  hostname does not appear either. Run with ``--tb=no``.
* **Only the two configured companies** (root ``CLAUDE.md`` §3).
  ``SIMPRO_LIVE_COMPANY_IDS`` (the allow-list, comma-separated) must equal
  ``SIMPRO_COMPANY_ID_SERVICE`` and ``SIMPRO_COMPANY_ID_PROJECTS``, or every
  test skips; the values live only in ``.env`` (ADR-017). Listing
  ``/companies/`` is allowed, and the request hook fails any request scoped
  to a company outside the allow-list before it is sent.

Run only when Alex asks::

    SIMPRO_LIVE_TESTS=1 uv run pytest -m live -v --tb=no -rN

``-rN`` drops the short summary too, whose exception messages can name the
build's host.

The expectations pin what the 2026-10-17 smoke check observed
(``docs/simpro/mock-vs-public-api.md`` §6), so a change upstream fails here.
"""

import logging
import os
import re
from collections.abc import Callable, Iterator

import httpx
import pytest
from pydantic import BaseModel, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from simpro_client.client import SimproClient
from simpro_client.config import SimproSettings

pytestmark = pytest.mark.live

#: The two companies CLIVE uses, by role (root ``CLAUDE.md`` §3). Tests are
#: parametrized by role so collection never depends on ``.env``.
COMPANY_ROLES = ["service", "projects"]

#: Collections Phase 3B reads per company, by client attribute.
COMPANY_COLLECTIONS = ["customers", "sites", "jobs", "quotes", "employees"]

PAGE_HEADERS = {"Result-Total", "Result-Count", "Result-Pages"}


class LiveTestSettings(BaseSettings):
    """The live tests' own company allow-list (ADR-017).

    Kept here rather than in ``SimproSettings``, because ``simpro_client``
    holds no CLIVE specifics (ADR-006).
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    simpro_live_company_ids: str = ""

    def company_ids(self) -> frozenset[int]:
        """The allow-list as integers; empty when unset or not all integers."""
        parts = [part.strip() for part in self.simpro_live_company_ids.split(",")]
        if not all(part.isdigit() for part in parts):
            return frozenset()
        return frozenset(int(part) for part in parts)


def request_guard(allowed: frozenset[int]) -> Callable[[httpx.Request], None]:
    """Build the request hook: only GETs, and only allowed companies."""

    def reject(request: httpx.Request) -> None:
        if request.method != "GET":
            pytest.fail(f"non-GET request blocked: {request.method}", pytrace=False)
        scope = re.search(r"/companies/(\d+)", request.url.path)
        if scope and int(scope.group(1)) not in allowed:
            pytest.fail("request to an unused company blocked", pytrace=False)

    return reject


@pytest.fixture(scope="module")
def live_settings() -> SimproSettings:
    """Live settings, or a skip when the opt-in or company IDs are missing."""
    if os.environ.get("SIMPRO_LIVE_TESTS") != "1":
        pytest.skip("live Simpro tests are opt-in: set SIMPRO_LIVE_TESTS=1")
    settings = SimproSettings()
    allowed = LiveTestSettings().company_ids()
    configured = {settings.company_id_service, settings.company_id_projects}
    if len(allowed) != 2 or configured != allowed:
        pytest.skip(
            "SIMPRO_LIVE_COMPANY_IDS must list exactly the two IDs in "
            "SIMPRO_COMPANY_ID_SERVICE/PROJECTS"
        )
    return settings


def company_id_for(settings: SimproSettings, role: str) -> int:
    """The configured company ID for a role in ``COMPANY_ROLES``."""
    return getattr(settings, f"company_id_{role}")


def open_client(settings: SimproSettings) -> SimproClient:
    """A client whose API traffic is GET-only and whose logging is silent."""
    allowed = frozenset({settings.company_id_service, settings.company_id_projects})
    client = SimproClient(settings=settings)
    client._logger.disabled = True
    client._http.event_hooks["request"].append(request_guard(allowed))
    return client


@pytest.fixture(scope="module")
def client(live_settings: SimproSettings) -> Iterator[SimproClient]:
    """One live client for the module, closed on teardown."""
    with open_client(live_settings) as live_client:
        yield live_client
    logging.getLogger("simpro_client").disabled = False


# Offline checks of the guards themselves: no network, no fixture, so they
# also run in the default suite.
@pytest.mark.parametrize(
    ("raw", "expected"),
    [("11,12", {11, 12}), (" 11 , 12 ", {11, 12}), ("", set()), ("11,x", set())],
)
def test_allow_list_parsing(monkeypatch: pytest.MonkeyPatch, raw: str, expected):
    """The allow-list is all integers or nothing; a bad entry disables it."""
    monkeypatch.setenv("SIMPRO_LIVE_COMPANY_IDS", raw)
    assert LiveTestSettings(_env_file=None).company_ids() == expected


def test_request_guard_allows_only_gets_to_allowed_companies():
    guard = request_guard(frozenset({11, 12}))
    base = "https://simpro.invalid/api/v1.0"
    guard(httpx.Request("GET", f"{base}/companies/"))
    guard(httpx.Request("GET", f"{base}/companies/11/jobs/"))
    with pytest.raises(pytest.fail.Exception):
        guard(httpx.Request("GET", f"{base}/companies/13/jobs/"))
    with pytest.raises(pytest.fail.Exception):
        guard(httpx.Request("POST", f"{base}/companies/11/jobs/"))


def validation_failures(model: type[BaseModel], rows: list[dict]) -> list[str]:
    """Validate rows and describe failures by location and type only."""
    failures = []
    for row in rows:
        try:
            model.model_validate(row)
        except ValidationError as exc:
            failures += [
                f"{'.'.join(map(str, err['loc']))}:{err['type']}"
                for err in exc.errors(include_input=False, include_url=False)
            ]
    return failures


def test_companies_list_is_unpaginated_and_holds_both_companies(
    client: SimproClient, live_settings: SimproSettings
):
    """Items 4 and 13: the token request works, ``/companies/`` sends no paging."""
    response = client._get_response("/companies/")

    assert response.status_code == 200
    assert "Result-Count" in response.headers
    paging = (PAGE_HEADERS - {"Result-Count"}) & set(response.headers)
    assert not paging, f"/companies/ now pages: headers {sorted(paging)}"
    # A bool, so a failure cannot echo any company ID (root §3, ADR-017).
    wanted = {company_id_for(live_settings, role) for role in COMPANY_ROLES}
    has_both = {row.get("ID") for row in response.json()} >= wanted
    assert has_both, "a configured company is missing from /companies/"

    page = client.companies.fetch_page()
    assert page.pages == 1
    assert page.count == len(page.items)


@pytest.mark.parametrize("role", COMPANY_ROLES)
@pytest.mark.parametrize("resource", COMPANY_COLLECTIONS)
def test_collection_pages_and_rows_validate(
    client: SimproClient, live_settings: SimproSettings, resource: str, role: str
):
    """Item 2: collections send the ``Result-*`` headers; rows fit the models."""
    company_id = company_id_for(live_settings, role)
    endpoint = getattr(client, resource)
    path = endpoint.collection_path.format(company_id=company_id)
    response = client._get_response(path, params={"page": 1, "pageSize": 5})

    assert response.status_code == 200
    missing = PAGE_HEADERS - set(response.headers)
    assert not missing, f"{resource}: missing headers {sorted(missing)}"
    rows = response.json()
    assert response.headers["Result-Count"] == str(len(rows))
    failures = validation_failures(endpoint.model, rows)
    assert not failures, f"{resource}: {failures}"


@pytest.mark.parametrize("role", COMPANY_ROLES)
def test_job_detail_validates(
    client: SimproClient, live_settings: SimproSettings, role: str
):
    """Item 17: a job detail validates, including ``""`` for empty dates."""
    company_id = company_id_for(live_settings, role)
    first = client.jobs.fetch_page(company_id=company_id, page_size=1).items
    if not first:
        pytest.skip(f"the {role} company has no jobs")
    path = client.jobs.detail_path.format(company_id=company_id, job_id=first[0].id)
    response = client._get_response(path)

    assert response.status_code == 200
    failures = validation_failures(client.jobs.model, [response.json()])
    assert not failures, f"job detail: {failures}"


def test_projection_does_not_add_id(
    client: SimproClient, live_settings: SimproSettings
):
    """Item 1: ``columns`` without ``ID`` returns only what was asked for.

    A raw request, so the client's own column additions (ADR-016) do not
    hide what the server does.
    """
    company_id = live_settings.company_id_service
    response = client._get_response(
        f"/companies/{company_id}/jobs/",
        params={"page": 1, "pageSize": 1, "columns": "Description"},
    )

    assert response.status_code == 200
    for row in response.json():
        assert set(row) == {"Description"}, f"projected keys {sorted(row)}"


@pytest.mark.parametrize("resource", COMPANY_COLLECTIONS)
def test_client_projection_validates(
    client: SimproClient, live_settings: SimproSettings, resource: str
):
    """ADR-016: the client adds the model's required fields to ``columns``.

    Asks for ``ID`` alone, so every other required field is the client's
    addition. For customers this includes ``_href``: whether Simpro accepts
    it as a column (rather than a 422) is unverified, and this settles it.
    """
    endpoint = getattr(client, resource)
    page = endpoint.fetch_page(
        company_id=live_settings.company_id_service, page_size=1, columns=["ID"]
    )

    assert page.count == len(page.items)


def test_token_survives_a_second_client(live_settings: SimproSettings):
    """Item 15: a second client's token request leaves the first token usable.

    Each ``SimproClient`` holds its own token (ADR-010). If Simpro revoked the
    older token when a newer one was issued, two workers would keep
    invalidating each other. The client recovers from a 401 by refreshing, so
    the check is that the first client's token is unchanged afterwards.
    """
    path = f"/companies/{live_settings.company_id_service}/employees/"
    params = {"page": 1, "pageSize": 1}
    with open_client(live_settings) as first, open_client(live_settings) as second:
        first_token = first._auth.get_token()
        assert first._get_response(path, params=params).status_code == 200
        assert second._get_response(path, params=params).status_code == 200
        assert first._get_response(path, params=params).status_code == 200
        # Compared, never printed: a bool keeps the tokens out of the output.
        unchanged = first._auth.get_token() == first_token
        assert unchanged, "first client had to refresh: older token revoked"
