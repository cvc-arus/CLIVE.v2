from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Status


class StatusesEndpoint(ResourceEndpoint[Status]):
    model = Status
    collection_path = "/companies/{company_id}/statuses/"
    detail_path = "/companies/{company_id}/statuses/{status_id}"
    item_key = "status_id"
