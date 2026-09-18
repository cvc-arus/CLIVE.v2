from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Contact


class ContactsEndpoint(ResourceEndpoint[Contact]):
    model = Contact
    collection_path = "/companies/{company_id}/customers/{customer_id}/contacts/"
    detail_path = (
        "/companies/{company_id}/customers/{customer_id}/contacts/{contact_id}"
    )
    item_key = "contact_id"
