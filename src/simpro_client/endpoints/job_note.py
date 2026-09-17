from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import JobNote


class JobNotesEndpoint(ResourceEndpoint[JobNote]):
    model = JobNote
    collection_path = "/companies/{company_id}/jobs/{job_id}/notes/"
    detail_path = "/companies/{company_id}/jobs/{job_id}/notes/{note_id}"
    item_key = "note_id"
