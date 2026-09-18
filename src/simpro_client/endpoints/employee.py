from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Employee


class EmployeesEndpoint(ResourceEndpoint[Employee]):
    model = Employee
    collection_path = "/companies/{company_id}/employees/"
    detail_path = "/companies/{company_id}/employees/{employee_id}"
    item_key = "employee_id"
