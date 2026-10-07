"""Reusable read-only endpoint behavior."""

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel

from simpro_client.exceptions import SimproProtocolError
from simpro_client.logging import get_correlation_id

if TYPE_CHECKING:
    from httpx import Headers

    from simpro_client.client import SimproClient

ModelT = TypeVar("ModelT", bound=BaseModel)
FilterValue = str | int | float | bool

#: Simpro's documented ceiling on ``pageSize`` (spec: ``minimum 1, maximum 250``).
MAX_PAGE_SIZE = 250

#: Simpro's documented default ``pageSize``.
DEFAULT_PAGE_SIZE = 30


@dataclass(frozen=True)
class Page(Generic[ModelT]):
    items: list[ModelT]
    page: int
    page_size: int
    total: int
    count: int
    pages: int


class ResourceEndpoint(Generic[ModelT]):
    model: type[ModelT]
    collection_path: str
    #: ``None`` for a collection Simpro publishes with no detail route, such
    #: as the polymorphic customers list. Such a subclass overrides ``get()``.
    detail_path: str | None
    item_key: str

    def __init__(self, client: "SimproClient") -> None:
        self._client = client

    def get(
        self,
        item_id: int | str,
        *,
        company_id: int | None = None,
        columns: Sequence[str] | None = None,
        **scope_ids: int,
    ) -> ModelT:
        """Fetch one resource by id.

        Args:
            item_id: The resource's ``ID``. A string for resources whose
                primary key is documented as a string, such as job attachments.
            company_id: The company scope, required by every route but
                ``/companies/``.
            columns: Optional ``columns`` projection. Simpro accepts it on
                detail routes as well as collections.
            **scope_ids: Any further route scopes, such as ``job_id``.

        Returns:
            The validated model.
        """
        values = self._route_values(company_id, scope_ids)
        values[self.item_key] = item_id
        path = self._render(self.detail_path, values)
        params = self._columns_param(columns)
        payload = self._client.get(path, params=params or None)
        return self.model.model_validate(payload)

    def fetch_page(
        self,
        *,
        company_id: int | None = None,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: Mapping[str, FilterValue] | None = None,
        columns: Sequence[str] | None = None,
        **scope_ids: int,
    ) -> Page[ModelT]:
        """Fetch one page of a collection.

        Args:
            company_id: The company scope.
            page: 1-based page number.
            page_size: Rows per page, 1 to ``MAX_PAGE_SIZE``.
            filters: Simpro filter parameters, keyed by their wire names.
            columns: Optional ``columns`` projection. Collection routes return
                a narrow default set of fields without it.
            **scope_ids: Any further route scopes.

        Returns:
            A :class:`Page` carrying the items and the server's counts.
        """
        values = self._route_values(company_id, scope_ids)
        path = self._render(self.collection_path, values)
        params = self._page_params(page, page_size, filters, columns)
        response = self._client._get_response(path, params=params)
        items = [self.model.model_validate(item) for item in response.json()]
        return Page(
            items=items,
            page=page,
            page_size=page_size,
            total=self._header_int(response.headers, "Result-Total", path),
            count=self._header_int(response.headers, "Result-Count", path),
            pages=self._header_int(response.headers, "Result-Pages", path),
        )

    def iter_all(
        self,
        *,
        company_id: int | None = None,
        page_size: int = DEFAULT_PAGE_SIZE,
        filters: Mapping[str, FilterValue] | None = None,
        columns: Sequence[str] | None = None,
        **scope_ids: int,
    ) -> Iterator[ModelT]:
        """Lazily iterate every row of a collection, one page at a time.

        Args:
            company_id: The company scope.
            page_size: Rows per page, 1 to ``MAX_PAGE_SIZE``.
            filters: Simpro filter parameters, keyed by their wire names.
            columns: Optional ``columns`` projection.
            **scope_ids: Any further route scopes.

        Yields:
            Each validated model, in server order.

        Raises:
            SimproProtocolError: On a missing or invalid ``Result-Pages``
                header, a page past the last page, or an empty page before it.
        """
        values = self._route_values(company_id, scope_ids)
        path = self._render(self.collection_path, values)
        page = 1
        while True:
            params = self._page_params(page, page_size, filters, columns)
            response = self._client._get_response(path, params=params)
            items = [self.model.model_validate(item) for item in response.json()]
            pages = self._header_int(response.headers, "Result-Pages", path)
            if pages < 1:
                raise self._protocol_error(f"Invalid Result-Pages={pages}", path)
            if page > pages:
                raise self._protocol_error(
                    f"Page {page} exceeds Result-Pages={pages}", path
                )
            if not items and page < pages:
                raise self._protocol_error(
                    f"Empty page {page} before Result-Pages={pages}", path
                )
            yield from items
            if page == pages:
                return
            page += 1

    @staticmethod
    def _columns_param(columns: Sequence[str] | None) -> dict[str, str]:
        """Render a ``columns`` projection as Simpro's csv query parameter.

        Args:
            columns: Wire-name column list, or ``None`` for the server default.

        Returns:
            ``{"columns": "A,B"}``, or an empty dict when nothing was asked for.
        """
        if not columns:
            return {}
        return {"columns": ",".join(columns)}

    @classmethod
    def _page_params(
        cls,
        page: int,
        page_size: int,
        filters: Mapping[str, FilterValue] | None,
        columns: Sequence[str] | None,
    ) -> dict[str, Any]:
        """Build the query parameters for one collection request.

        Args:
            page: 1-based page number.
            page_size: Rows per page.
            filters: Simpro filter parameters, keyed by their wire names.
            columns: Optional ``columns`` projection.

        Returns:
            The query parameters, with ``page`` and ``pageSize`` in the
            camelCase spelling Simpro expects.

        Raises:
            ValueError: If ``page`` or ``page_size`` is outside the documented
                range. Simpro's spec declares ``pageSize`` as
                ``minimum 1, maximum 250``, so sending more is rejected
                server-side rather than clamped.
        """
        if page < 1:
            raise ValueError(f"page must be >= 1, got {page}")
        if not 1 <= page_size <= MAX_PAGE_SIZE:
            raise ValueError(
                f"page_size must be between 1 and {MAX_PAGE_SIZE}, got {page_size}"
            )
        params: dict[str, Any] = dict(filters or {})
        params.update(page=page, pageSize=page_size)
        params.update(cls._columns_param(columns))
        return params

    @staticmethod
    def _route_values(company_id, scope_ids):
        values = dict(scope_ids)
        if company_id is not None:
            values["company_id"] = company_id
        return values

    @staticmethod
    def _render(template, values):
        try:
            return template.format(**values)
        except KeyError as exc:
            raise ValueError(f"Missing route parameter: {exc.args[0]}") from exc

    @classmethod
    def _header_int(cls, headers: "Headers", name: str, path: str) -> int:
        value = headers.get(name)
        if value is None:
            raise cls._protocol_error(f"Missing pagination header: {name}", path)
        try:
            return int(value)
        except ValueError as exc:
            raise cls._protocol_error(f"Invalid pagination header: {name}", path) from exc

    @staticmethod
    def _protocol_error(message: str, path: str) -> SimproProtocolError:
        return SimproProtocolError(message, method="GET", url=path, correlation_id=get_correlation_id())
