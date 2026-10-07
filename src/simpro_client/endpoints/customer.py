"""Customer endpoints. Simpro exposes three, not one.

``/customers/`` lists both kinds together and carries a ``Type`` discriminator
plus an ``_href``; the full record lives on a subtype route. So a caller lists
from :class:`CustomersEndpoint` and then fetches from
:class:`IndividualCustomersEndpoint` or :class:`CompanyCustomersEndpoint`
according to ``Type`` (ADR-013 decision 2).
"""

from typing import Any, NoReturn

from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import CompanyCustomer, CustomerSummary, IndividualCustomer


class CustomersEndpoint(ResourceEndpoint[CustomerSummary]):
    """The polymorphic customer collection. **List only.**

    Simpro publishes no ``/customers/{id}`` detail route, so ``get()`` raises
    instead of building a URL that would 404.
    """

    model = CustomerSummary
    collection_path = "/companies/{company_id}/customers/"
    #: No detail route exists upstream; ``get()`` is overridden to say so.
    detail_path = None
    item_key = "customer_id"

    def get(self, *args: Any, **kwargs: Any) -> NoReturn:
        """Always raise: this collection has no detail route.

        Raises:
            NotImplementedError: Always, naming the two endpoints that do have
                one.
        """
        raise NotImplementedError(
            "Simpro has no /customers/{id} route. Use the Type discriminator "
            "from the list response and fetch from client.individual_customers "
            "or client.company_customers."
        )


class IndividualCustomersEndpoint(ResourceEndpoint[IndividualCustomer]):
    """Customers who are people."""

    model = IndividualCustomer
    collection_path = "/companies/{company_id}/customers/individuals/"
    detail_path = "/companies/{company_id}/customers/individuals/{customer_id}"
    item_key = "customer_id"


class CompanyCustomersEndpoint(ResourceEndpoint[CompanyCustomer]):
    """Customers that are organisations."""

    model = CompanyCustomer
    collection_path = "/companies/{company_id}/customers/companies/"
    detail_path = "/companies/{company_id}/customers/companies/{customer_id}"
    item_key = "customer_id"
