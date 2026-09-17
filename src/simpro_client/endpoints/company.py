from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Company


class CompaniesEndpoint(ResourceEndpoint[Company]):
    model = Company
    collection_path = "/companies/"
    detail_path = "/companies/{company_id}"
    item_key = "company_id"
