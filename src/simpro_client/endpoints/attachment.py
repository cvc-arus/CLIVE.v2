from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Attachment


class AttachmentsEndpoint(ResourceEndpoint[Attachment]):
    model = Attachment
    collection_path = "/companies/{company_id}/jobs/{job_id}/attachments/"
    detail_path = (
        "/companies/{company_id}/jobs/{job_id}/attachments/{attachment_id}"
    )
    item_key = "attachment_id"
