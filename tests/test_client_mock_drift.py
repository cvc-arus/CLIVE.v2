"""Prove that ``simpro_client`` can actually talk to ``simpro_mock``.

Before this module, nothing did. ``test_simpro_mock_v2.py`` drives the mock with
raw ``httpx`` and never imports the client; every client-side test uses
``respx`` and never touches the mock. So the two packages could drift apart —
a renamed route on one side, a renamed field on the other — and the whole suite
would stay green.

That matters most during the re-shape to Simpro's published spec (ADR-013),
where routes, field names and types all move. Each sprint changes both sides,
and this module is what fails if only one of them lands.

It asserts the join, not the payloads: every endpoint registered on
``SimproClient`` is reachable at the path the mock serves, returns the declared
model, and paginates with the ``Result-*`` headers. Per ``tests/CLAUDE.md`` §4
it never asserts exact seeded values — only shapes and stable invariants.
"""

from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest

from simpro_client import SimproClient, SimproSettings
from simpro_client.endpoints.base import ResourceEndpoint

pytestmark = pytest.mark.integration

BASE = "http://localhost:8100"

#: Endpoint attributes on ``SimproClient`` and the scopes they need beyond
#: ``company_id``. Scope values are discovered from the mock at runtime, never
#: hardcoded, so the seed can change freely.
SCOPES: dict[str, tuple[str, ...]] = {
    "companies": (),
    "customers": (),
    "jobs": (),
    "quotes": (),
    "sites": (),
    "employees": (),
    "projects": (),
    "statuses": (),
    "contacts": ("customer_id",),
    "assets": ("site_id",),
    "job_notes": ("job_id",),
    "attachments": ("job_id",),
}


@pytest.fixture(scope="module", autouse=True)
def require_mock() -> None:
    """Skip at test runtime, never while pytest imports or collects."""
    try:
        httpx.get(f"{BASE}/health", timeout=1.0).raise_for_status()
    except httpx.HTTPError:
        pytest.skip(
            "simpro-mock is not running on localhost:8100 "
            "(start it with: docker compose up -d simpro-mock)"
        )


@pytest.fixture(scope="module")
def settings() -> SimproSettings:
    """Settings pointing at the locally published mock port."""
    return SimproSettings(
        base_url=f"{BASE}/api/v1.0",
        token_url=f"{BASE}/oauth2/token",
        client_id="drift-test",
        client_secret="drift-test",
        auth_mode="client_credentials",
    )


@pytest.fixture(scope="module")
def client(settings: SimproSettings) -> Iterator[SimproClient]:
    """One client for the module, closed on teardown."""
    with SimproClient(settings=settings) as open_client:
        yield open_client


@pytest.fixture(scope="module")
def scope_ids(client: SimproClient) -> dict[str, int]:
    """Discover a usable company, customer, site and job from the mock."""
    companies = client.companies.fetch_page(page_size=1)
    assert companies.items, "the mock seeded no companies"
    company_id = companies.items[0].id

    discovered = {"company_id": company_id}
    for key, attribute in (
        ("customer_id", "customers"),
        ("site_id", "sites"),
        ("job_id", "jobs"),
    ):
        page = getattr(client, attribute).fetch_page(company_id=company_id, page_size=1)
        assert page.items, f"the mock seeded no {attribute} for company {company_id}"
        discovered[key] = page.items[0].id
    return discovered


def _endpoint_scope(
    name: str, scope_ids: dict[str, int]
) -> tuple[dict[str, int], int | None]:
    """Return the keyword scope for an endpoint, and its company_id."""
    company_id = None if name == "companies" else scope_ids["company_id"]
    scope = {key: scope_ids[key] for key in SCOPES[name]}
    return scope, company_id


def test_every_registered_endpoint_is_covered(client: SimproClient) -> None:
    """``SCOPES`` lists exactly the endpoints the client registers.

    Guards against a new or renamed endpoint silently escaping this module.
    """
    registered = {
        name
        for name in vars(client)
        if isinstance(getattr(client, name), ResourceEndpoint)
    }
    assert registered == set(SCOPES), (
        f"SCOPES is out of step with SimproClient: "
        f"missing {sorted(registered - set(SCOPES))}, "
        f"stale {sorted(set(SCOPES) - registered)}"
    )


@pytest.mark.parametrize("name", sorted(SCOPES))
def test_endpoint_lists_against_the_mock(
    client: SimproClient, scope_ids: dict[str, int], name: str
) -> None:
    """Each endpoint's collection route resolves and parses into its model."""
    scope, company_id = _endpoint_scope(name, scope_ids)
    endpoint = getattr(client, name)

    page = endpoint.fetch_page(company_id=company_id, page_size=5, **scope)

    assert page.items, f"{name}: the mock returned an empty first page"
    assert all(isinstance(item, endpoint.model) for item in page.items)
    assert page.total >= len(page.items)
    assert page.pages >= 1
    assert page.count == len(page.items)


@pytest.mark.parametrize("name", sorted(SCOPES))
def test_endpoint_detail_against_the_mock(
    client: SimproClient, scope_ids: dict[str, int], name: str
) -> None:
    """Each endpoint's detail route resolves for an id taken from its list."""
    scope, company_id = _endpoint_scope(name, scope_ids)
    endpoint = getattr(client, name)

    page = endpoint.fetch_page(company_id=company_id, page_size=1, **scope)
    assert page.items, f"{name}: the mock returned an empty first page"

    item = endpoint.get(page.items[0].id, company_id=company_id, **scope)

    assert isinstance(item, endpoint.model)
    assert item.id == page.items[0].id


@pytest.mark.parametrize("name", sorted(SCOPES))
def test_endpoint_iter_all_against_the_mock(
    client: SimproClient, scope_ids: dict[str, int], name: str
) -> None:
    """``iter_all`` walks every page without a pagination protocol error."""
    scope, company_id = _endpoint_scope(name, scope_ids)
    endpoint = getattr(client, name)

    page = endpoint.fetch_page(company_id=company_id, page_size=2, **scope)
    walked = list(endpoint.iter_all(company_id=company_id, page_size=2, **scope))

    assert len(walked) == page.total
    assert all(isinstance(item, endpoint.model) for item in walked)
