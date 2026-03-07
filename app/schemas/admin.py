from datetime import datetime
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class JobResponse(BaseModel):
    id: int
    tenant_id: int
    connection_id: int
    job_type: str
    is_enabled: bool


class JobRunResponse(BaseModel):
    id: int
    job_id: int
    status: str
    correlation_id: str
    started_at: datetime | None
    finished_at: datetime | None
    records_raw: int
    records_normalized: int


class ErrorResponse(BaseModel):
    id: int
    tenant_id: int
    job_run_id: int | None
    object_name: str
    message: str
    severity: str
    created_at: datetime
