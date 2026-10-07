from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import ProjectStatusCode


class ProjectStatusCodesEndpoint(ResourceEndpoint[ProjectStatusCode]):
    model = ProjectStatusCode
    collection_path = "/companies/{company_id}/setup/statusCodes/projects/"
    detail_path = "/companies/{company_id}/setup/statusCodes/projects/{status_code_id}"
    item_key = "status_code_id"
