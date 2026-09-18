from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Project


class ProjectsEndpoint(ResourceEndpoint[Project]):
    model = Project
    collection_path = "/companies/{company_id}/projects/"
    detail_path = "/companies/{company_id}/projects/{project_id}"
    item_key = "project_id"
