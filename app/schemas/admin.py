from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.connectors.base import ConnectorMode


class HealthResponse(BaseModel):
    status: str
    service: str


class TenantResponse(BaseModel):
    id: int
    slug: str
    name: str
    is_active: bool


class TenantCreateRequest(BaseModel):
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    name: str = Field(min_length=1, max_length=200)


class TenantUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None


class ProviderJobResponse(BaseModel):
    job_type: str
    label: str
    description: str


class ProviderResponse(BaseModel):
    key: str
    display_name: str
    description: str
    environments: list[str]
    default_environment: str
    default_base_urls: dict[str, str]
    docs_url: str | None = None
    jobs: list[ProviderJobResponse]


class OnboardingStepResponse(BaseModel):
    key: str
    label: str
    done: bool
    detail: str


class ConnectionOnboardingResponse(BaseModel):
    ready: bool
    progress: int
    next_action: str | None = None
    steps: list[OnboardingStepResponse]


class ConnectorCreateRequest(BaseModel):
    provider: str
    name: str | None = None
    mode: ConnectorMode = ConnectorMode.MOCK
    environment: str | None = None
    base_url: str | None = None
    secret_ref: str | None = None
    api_key: str | None = None
    priority: int | None = None
    is_primary: bool = False
    config_payload: dict[str, Any] | None = None


class ConnectorConfigUpdate(BaseModel):
    name: str | None = None
    mode: ConnectorMode | None = None
    environment: str | None = None
    base_url: str | None = None
    secret_ref: str | None = None
    api_key: str | None = None
    priority: int | None = None
    is_primary: bool | None = None
    is_active: bool | None = None
    config_payload: dict[str, Any] | None = None


class ConnectorModeUpdate(BaseModel):
    mode: str
    base_url: str | None = None
    secret_ref: str | None = None
    api_key: str | None = None
    check_connection: bool = True


class AdminConnectionResponse(BaseModel):
    id: int
    tenant_id: int
    provider: str
    provider_label: str
    name: str
    mode: ConnectorMode
    environment: str
    base_url: str
    is_active: bool
    is_primary: bool
    priority: int
    has_secret: bool
    provider_account_id: str | None = None
    status: str
    last_checked_at: datetime | None = None
    last_check_ok: bool | None = None
    last_check_message: str | None = None
    jobs_total: int = 0
    jobs_enabled: int = 0
    last_sync_at: datetime | None = None
    last_run_status: str | None = None
    recent_error_count: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    onboarding: ConnectionOnboardingResponse
    connected: bool | None = None
    message: str | None = None


class JobResponse(BaseModel):
    id: int
    tenant_id: int
    connection_id: int
    connection_name: str
    provider: str
    provider_label: str
    job_type: str
    job_label: str
    is_enabled: bool


class JobRunResponse(BaseModel):
    id: int
    job_id: int
    connection_id: int
    connection_name: str
    provider: str
    provider_label: str
    job_type: str
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
    payload: dict[str, Any] | None = Field(default=None)
    created_at: datetime


class MappingResponse(BaseModel):
    id: int
    tenant_id: int
    connection_id: int | None
    provider: str
    object_name: str
    version: str
    mapping_payload: dict[str, Any]
    is_active: bool


class ConnectorJobsResponse(BaseModel):
    connection_id: int
    jobs_total: int
    jobs_enabled: int
    jobs: list[JobResponse]


class ConnectorBatchRunResponse(BaseModel):
    connection_id: int
    queued_runs: list[JobRunResponse]
    message: str


class AuditLogResponse(BaseModel):
    id: int
    tenant_id: int | None
    actor: str
    action: str
    target_type: str
    target_id: str | None
    target_label: str | None
    payload: dict[str, Any] | None = None
    created_at: datetime


class OverviewConnectionResponse(BaseModel):
    connection_id: int
    provider: str
    provider_label: str
    name: str
    environment: str
    mode: ConnectorMode
    status: str
    is_primary: bool
    jobs_enabled: int
    jobs_total: int
    last_sync_at: datetime | None = None
    last_run_status: str | None = None
    recent_error_count: int = 0


class TenantOverviewResponse(BaseModel):
    tenant: TenantResponse
    totals: dict[str, int | str | None]
    providers: list[OverviewConnectionResponse]


class ConnectorCheckResponse(BaseModel):
    connection: AdminConnectionResponse
