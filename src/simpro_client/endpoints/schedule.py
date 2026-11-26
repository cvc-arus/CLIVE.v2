from simpro_client.endpoints.base import ResourceEndpoint
from simpro_client.models import Schedule


class SchedulesEndpoint(ResourceEndpoint[Schedule]):
    model = Schedule
    collection_path = "/companies/{company_id}/schedules/"
    detail_path = "/companies/{company_id}/schedules/{schedule_id}"
    item_key = "schedule_id"
