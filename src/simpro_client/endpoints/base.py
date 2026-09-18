"""Reusable read-only endpoint behavior."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import BaseModel

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

    def get(
        self,
        item_id: int,
        *,
        company_id: int | None = None,
        **scope_ids: int,
    ) -> ModelT:
        values = self._route_values(company_id, scope_ids)
        values[self.item_key] = item_id
        payload = self._client.get(self._render(self.detail_path, values))
        return self.model.model_validate(payload)

    def fetch_page(
        self,
        *,
        company_id: int | None = None,
        page: int = 1,
        page_size: int = 30,
        filters: Mapping[str, FilterValue] | None = None,
        **scope_ids: int,
    ) -> Page[ModelT]:
        values = self._route_values(company_id, scope_ids)
        params: dict[str, Any] = dict(filters or {})
        params["page"] = page
        params["pageSize"] = page_size
        response = self._client._get_response(
            self._render(self.collection_path, values), params=params
        )
        items = [self.model.model_validate(item) for item in response.json()]
        return Page(
            items=items,
            page=page,
            page_size=page_size,
            total=self._header_int(response.headers, "Result-Total"),
            count=self._header_int(response.headers, "Result-Count"),
            pages=self._header_int(response.headers, "Result-Pages"),
        )

    @staticmethod
    def _route_values(
        company_id: int | None, scope_ids: Mapping[str, int]
    ) -> dict[str, int]:
        values = dict(scope_ids)
        if company_id is not None:
            values["company_id"] = company_id
        return values

    @staticmethod
    def _render(template: str, values: Mapping[str, int]) -> str:
        try:
            return template.format(**values)
        except KeyError as exc:
            raise ValueError(f"Missing route parameter: {exc.args[0]}") from exc

    @staticmethod
    def _header_int(headers: "Headers", name: str) -> int:
        try:
            return int(headers[name])
        except KeyError as exc:
            raise ValueError(f"Missing pagination header: {name}") from exc
        except ValueError as exc:
            raise ValueError(f"Invalid pagination header: {name}") from exc
