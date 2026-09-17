from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Customer


class CustomersEndpoint(ResourceEndpoint[Customer]):
    model = Customer
    collection_path = "/companies/{company_id}/customers/"
    detail_path = "/companies/{company_id}/customers/{customer_id}"
    item_key = "customer_id"
