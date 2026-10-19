from collections.abc import Iterator, Mapping, Sequence
from typing import Any

from simpro_client.endpoints.base import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    FilterValue,
    Page,
    ResourceEndpoint,
)
from simpro_client.models import Company


class CompaniesEndpoint(ResourceEndpoint[Company]):
    """The build's companies.

    ``/companies/`` is **not paginated** upstream: the contract documents no
    ``page``, ``pageSize`` or ``limit`` on it, and live Simpro returns every
    company in one response with only a ``Result-Count`` header (no
    ``Result-Total`` or ``Result-Pages``; ``docs/simpro/mock-vs-public-api.md``
    §6, item 4). So the collection methods make one request without paging
    parameters, and the base class's header checks do not apply.
    """

    model = Company
    collection_path = "/companies/"
    detail_path = "/companies/{company_id}"
    item_key = "company_id"

    def fetch_page(
        self,
        *,
        company_id: int | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: Mapping[str, FilterValue] | None = None,
        columns: Sequence[str] | None = None,
        **scope_ids: int,
    ) -> Page[Company]:
        """Fetch every company in one request, as a single page.

        Args:
            company_id: Unused; ``/companies/`` has no company scope. Accepted
                so the signature matches :meth:`ResourceEndpoint.fetch_page`.
            page: Must be 1, since there is only one page.
            page_size: Validated against the documented range but **not
                sent**: Simpro returns every company regardless.
            filters: Simpro filter parameters, keyed by their wire names.
            columns: Optional ``columns`` projection.
            **scope_ids: Unused, as for ``company_id``.

        Returns:
            A :class:`Page` holding every company, with ``total`` and
            ``count`` both taken from ``Result-Count``, ``page`` and
            ``pages`` both 1, and ``page_size`` equal to the row count.

        Raises:
            ValueError: If ``page`` is not 1 or ``page_size`` is out of range.
            SimproProtocolError: On a missing or invalid ``Result-Count``.
        """
        if page != 1:
            raise ValueError(
                f"/companies/ is not paginated; page must be 1, got {page}"
            )
        if not 1 <= page_size <= MAX_PAGE_SIZE:
            raise ValueError(
                f"page_size must be between 1 and {MAX_PAGE_SIZE}, got {page_size}"
            )
        path = self.collection_path
        params: dict[str, Any] = dict(filters or {})
        params.update(self._columns_param(columns))
        response = self._client._get_response(path, params=params)
        items = [self.model.model_validate(item) for item in response.json()]
        count = self._header_int(response.headers, "Result-Count", path)
        return Page(
            items=items,
            page=1,
            page_size=len(items),
            total=count,
            count=count,
            pages=1,
        )

    def iter_all(
        self,
        *,
        company_id: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: Mapping[str, FilterValue] | None = None,
        columns: Sequence[str] | None = None,
        **scope_ids: int,
    ) -> Iterator[Company]:
        """Lazily iterate every company, from one request.

        Args:
            company_id: Unused; see :meth:`fetch_page`.
            page_size: Validated but not sent; see :meth:`fetch_page`.
            filters: Simpro filter parameters, keyed by their wire names.
            columns: Optional ``columns`` projection.
            **scope_ids: Unused.

        Yields:
            Each validated company, in server order.

        Raises:
            SimproProtocolError: On a missing or invalid ``Result-Count``.
        """
        yield from self.fetch_page(
            page_size=page_size, filters=filters, columns=columns
        ).items
