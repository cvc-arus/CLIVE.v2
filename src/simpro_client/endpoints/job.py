from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Job


class JobsEndpoint(ResourceEndpoint[Job]):
    model = Job
    collection_path = "/companies/{company_id}/jobs/"
    detail_path = "/companies/{company_id}/jobs/{job_id}"
    item_key = "job_id"
