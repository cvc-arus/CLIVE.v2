"""Reusable read-only endpoint behavior."""

from collections.abc import Iterator, Mapping
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
    detail_path: str
    item_key: str

    def __init__(self, client: "SimproClient") -> None:
        self._client = client

    def get(self, item_id: int, *, company_id: int | None = None, **scope_ids: int) -> ModelT:
        values = self._route_values(company_id, scope_ids)
        values[self.item_key] = item_id
        payload = self._client.get(self._render(self.detail_path, values))
        return self.model.model_validate(payload)

    def fetch_page(self, *, company_id: int | None = None, page: int = 1, page_size: int = 30, filters: Mapping[str, FilterValue] | None = None, **scope_ids: int) -> Page[ModelT]:
        values = self._route_values(company_id, scope_ids)
        path = self._render(self.collection_path, values)
        params: dict[str, Any] = dict(filters or {})
        params.update(page=page, pageSize=page_size)
        response = self._client._get_response(path, params=params)
        items = [self.model.model_validate(item) for item in response.json()]
        return Page(items=items, page=page, page_size=page_size, total=self._header_int(response.headers, "Result-Total", path), count=self._header_int(response.headers, "Result-Count", path), pages=self._header_int(response.headers, "Result-Pages", path))

    def iter_all(self, *, company_id: int | None = None, page_size: int = 30, filters: Mapping[str, FilterValue] | None = None, **scope_ids: int) -> Iterator[ModelT]:
        values = self._route_values(company_id, scope_ids)
        path = self._render(self.collection_path, values)
        page = 1
        while True:
            params: dict[str, Any] = dict(filters or {})
            params.update(page=page, pageSize=page_size)
            response = self._client._get_response(path, params=params)
            items = [self.model.model_validate(item) for item in response.json()]
            pages = self._header_int(response.headers, "Result-Pages", path)
            if pages < 1:
                raise self._protocol_error(f"Invalid Result-Pages={pages}", path)
            if page > pages:
                raise self._protocol_error(f"Page {page} exceeds Result-Pages={pages}", path)
            if not items and page < pages:
                raise self._protocol_error(f"Empty page {page} before Result-Pages={pages}", path)
            yield from items
            if page == pages:
                return
            page += 1

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
