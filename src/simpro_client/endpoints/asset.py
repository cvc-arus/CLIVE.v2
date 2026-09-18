from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Asset


class AssetsEndpoint(ResourceEndpoint[Asset]):
    model = Asset
    collection_path = "/companies/{company_id}/sites/{site_id}/assets/"
    detail_path = "/companies/{company_id}/sites/{site_id}/assets/{asset_id}"
    item_key = "asset_id"
