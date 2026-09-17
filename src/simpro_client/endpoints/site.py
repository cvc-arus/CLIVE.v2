from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Site


class SitesEndpoint(ResourceEndpoint[Site]):
    model = Site
    collection_path = "/companies/{company_id}/sites/"
    detail_path = "/companies/{company_id}/sites/{site_id}"
    item_key = "site_id"
