from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.connectors.base import ConnectionStatus, ConnectorConfig, ConnectorConfigurationError, ConnectorMode
from app.connectors.bsale import (
    attempt_bsale_connection,
    build_bsale_config,
    build_bsale_job_connector,
    probe_bsale_connection,
    resolve_mock_base_url,
    resolve_real_base_url,
)
from app.models import IntegrationConnection
from app.normalizers.bsale import (
    normalize_branch,
    normalize_client,
    normalize_document_type,
    normalize_product,
    normalize_sales_document,
    normalize_stock,
)
from app.providers.base import ProviderCheckResult, ProviderDefinition, ProviderJobDefinition
from app.secrets import SecretStore


class BsaleProvider(ProviderDefinition):
    key = "bsale"
    display_name = "Bsale"
    description = "Conector de catalogo, clientes, tipos de documento, stock, ventas y sucursales via API Bsale."
    environments = ("mock", "production")
    default_environment = "production"
    docs_url = "https://api.bsale.cl"
    _jobs = (
        ProviderJobDefinition(
            job_type="sync_product_catalog",
            label="Catalogo",
            description="Trae productos, variantes e impuestos asociados y normaliza el catalogo canonico.",
        ),
        ProviderJobDefinition(
            job_type="sync_customers",
            label="Clientes",
            description="Trae clientes con contactos, direcciones y atributos asociados.",
        ),
        ProviderJobDefinition(
            job_type="sync_document_types",
            label="Tipos de documento",
            description="Sincroniza tipos de documento configurados en Bsale para referencias y validaciones.",
        ),
        ProviderJobDefinition(
            job_type="sync_stock_snapshot",
            label="Stock",
            description="Captura snapshot de stock por producto y sucursal.",
        ),
        ProviderJobDefinition(
            job_type="sync_sales_documents",
            label="Documentos",
            description="Importa documentos (boletas, facturas, NC) con detalles, montos neto/iva y tipo.",
        ),
        ProviderJobDefinition(
            job_type="sync_branches",
            label="Sucursales",
            description="Sincroniza oficinas o sucursales del proveedor.",
        ),
    )

    @property
    def jobs(self) -> tuple[ProviderJobDefinition, ...]:
        return self._jobs

    def default_connection_name(self, *, ordinal: int) -> str:
        return "Bsale principal" if ordinal <= 1 else f"Bsale {ordinal}"

    def default_base_url(self, *, mode: ConnectorMode) -> str:
        if mode == ConnectorMode.MOCK:
            return resolve_mock_base_url()
        return resolve_real_base_url()

    def apply_configuration(
        self,
        db: Session,
        conn: IntegrationConnection,
        payload: dict[str, Any],
        *,
        secret_store: SecretStore,
    ) -> str:
        requested_mode = payload.get("mode") or ConnectorMode(conn.mode)
        if not isinstance(requested_mode, ConnectorMode):
            requested_mode = ConnectorMode(requested_mode)

        conn.name = self._clean(payload.get("name")) or conn.name or self.default_connection_name(ordinal=1)
        conn.mode = requested_mode.value
        conn.environment = self._clean(payload.get("environment")) or ("mock" if requested_mode == ConnectorMode.MOCK else "production")

        if payload.get("priority") is not None:
            conn.priority = int(payload["priority"])
        if payload.get("is_active") is not None:
            conn.is_active = bool(payload["is_active"])
        if payload.get("config_payload") is not None:
            conn.config_payload = payload.get("config_payload") or None

        token_candidate = payload.get("api_key") if payload.get("api_key") is not None else payload.get("secret_ref")
        if token_candidate is not None and self._clean(token_candidate):
            conn.secret_ref = secret_store.save(
                db,
                value=token_candidate,
                tenant_id=conn.tenant_id,
                provider=conn.provider,
                current_ref=conn.secret_ref,
            )

        if requested_mode == ConnectorMode.MOCK:
            conn.base_url = self._clean_base_url(payload.get("base_url")) or self.default_base_url(mode=ConnectorMode.MOCK)
            conn.status = ConnectionStatus.MOCK.value
            conn.last_checked_at = None
            conn.last_check_ok = None
            conn.last_check_message = "Modo mock habilitado; la conexion opera contra el mock local."
            return conn.last_check_message

        if payload.get("base_url") is not None:
            conn.base_url = self._clean_base_url(payload.get("base_url")) or ""
        elif not conn.base_url or "mock-bsale-api" in conn.base_url:
            conn.base_url = self.default_base_url(mode=ConnectorMode.REAL)

        conn.status = self._status_for_saved_config(conn.base_url, secret_store.resolve(db, conn.secret_ref)).value
        conn.last_checked_at = None
        conn.last_check_ok = None
        if conn.status == ConnectionStatus.CONFIG_INCOMPLETE.value:
            missing = self._missing_real_fields(conn.base_url, secret_store.resolve(db, conn.secret_ref))
            conn.last_check_message = "Falta configuracion para modo real de Bsale: " + ", ".join(missing)
            return conn.last_check_message

        conn.last_check_message = "Configuracion real guardada. Ejecuta 'Probar conexion' para validar la cuenta."
        return conn.last_check_message

    def check_connection(
        self,
        db: Session,
        conn: IntegrationConnection,
        *,
        secret_store: SecretStore,
    ) -> ProviderCheckResult:
        checked_at = datetime.utcnow()
        mode = ConnectorMode(conn.mode)
        if mode == ConnectorMode.MOCK:
            message = "Modo mock habilitado; no se valida conectividad real."
            conn.status = ConnectionStatus.MOCK.value
            conn.last_checked_at = checked_at
            conn.last_check_ok = True
            conn.last_check_message = message
            return ProviderCheckResult(connected=True, message=message, checked_at=checked_at)

        api_key = secret_store.resolve(db, conn.secret_ref)
        missing = self._missing_real_fields(conn.base_url, api_key)
        if missing:
            message = "Falta configuracion para modo real de Bsale: " + ", ".join(missing)
            conn.status = ConnectionStatus.CONFIG_INCOMPLETE.value
            conn.last_checked_at = checked_at
            conn.last_check_ok = False
            conn.last_check_message = message
            return ProviderCheckResult(connected=False, message=message, checked_at=checked_at)

        try:
            config = build_bsale_config(
                mode=ConnectorMode.REAL,
                base_url=conn.base_url,
                api_key=api_key,
                current=ConnectorConfig(name=conn.provider, mode=mode, base_url=conn.base_url, api_key=api_key),
            )
        except ConnectorConfigurationError as exc:
            message = str(exc)
            conn.status = ConnectionStatus.CONFIG_INCOMPLETE.value
            conn.last_checked_at = checked_at
            conn.last_check_ok = False
            conn.last_check_message = message
            return ProviderCheckResult(connected=False, message=message, checked_at=checked_at)

        connected, message, payload = probe_bsale_connection(config)
        conn.status = self._status_for_check_result(connected=connected, message=message).value
        conn.last_checked_at = checked_at
        conn.last_check_ok = connected
        conn.last_check_message = message
        provider_account_id = self._extract_company_id(payload)
        if provider_account_id:
            conn.provider_account_id = provider_account_id
        return ProviderCheckResult(
            connected=connected,
            message=message,
            provider_account_id=provider_account_id,
            checked_at=checked_at,
        )

    def build_runtime_connector(
        self,
        db: Session,
        conn: IntegrationConnection,
        *,
        secret_store: SecretStore,
    ):
        return build_bsale_job_connector(
            mode=conn.mode,
            base_url=conn.base_url,
            api_key=secret_store.resolve(db, conn.secret_ref),
        )

    def normalize(self, job_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if job_type == "sync_product_catalog":
            return normalize_product(payload)
        if job_type == "sync_customers":
            return normalize_client(payload)
        if job_type == "sync_document_types":
            return normalize_document_type(payload)
        if job_type == "sync_stock_snapshot":
            return normalize_stock(payload)
        if job_type == "sync_sales_documents":
            return normalize_sales_document(payload)
        if job_type == "sync_branches":
            return normalize_branch(payload)
        raise ValueError(f"unsupported job type {job_type}")

    def source_endpoint_for_job(self, job_type: str) -> str:
        return {
            "sync_product_catalog": "products.json",
            "sync_customers": "clients.json",
            "sync_document_types": "document_types.json",
            "sync_stock_snapshot": "stocks.json",
            "sync_sales_documents": "documents.json",
            "sync_branches": "offices.json",
        }[job_type]

    @staticmethod
    def _clean(value: Any) -> str | None:
        if value is None:
            return None
        candidate = str(value).strip()
        return candidate or None

    @classmethod
    def _clean_base_url(cls, value: Any) -> str | None:
        candidate = cls._clean(value)
        return candidate.rstrip("/") if candidate else None

    @classmethod
    def _missing_real_fields(cls, base_url: str | None, api_key: str | None) -> list[str]:
        missing: list[str] = []
        if not cls._clean_base_url(base_url):
            missing.append("base_url")
        if not cls._clean(api_key):
            missing.append("api_key")
        return missing

    @classmethod
    def _status_for_saved_config(cls, base_url: str | None, api_key: str | None) -> ConnectionStatus:
        return ConnectionStatus.CONFIG_INCOMPLETE if cls._missing_real_fields(base_url, api_key) else ConnectionStatus.CONFIGURED

    @staticmethod
    def _status_for_check_result(*, connected: bool, message: str) -> ConnectionStatus:
        if connected:
            return ConnectionStatus.HEALTHY
        lowered = message.lower()
        if "401" in message or "authenticated" in lowered or "token" in lowered:
            return ConnectionStatus.AUTH_FAILED
        return ConnectionStatus.CONNECTION_ERROR

    @staticmethod
    def _extract_company_id(payload: dict[str, Any] | None) -> str | None:
        if not isinstance(payload, dict):
            return None
        for key in ("id", "company_id", "companyId"):
            value = payload.get(key)
            if value is not None:
                return str(value)
        return None
