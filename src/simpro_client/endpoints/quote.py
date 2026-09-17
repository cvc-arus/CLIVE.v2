from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Quote


class QuotesEndpoint(ResourceEndpoint[Quote]):
    model = Quote
    collection_path = "/companies/{company_id}/quotes/"
    detail_path = "/companies/{company_id}/quotes/{quote_id}"
    item_key = "quote_id"
