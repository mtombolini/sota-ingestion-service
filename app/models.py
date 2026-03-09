from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class IntegrationConnection(Base):
    __tablename__ = "integration_connections"
    __table_args__ = (UniqueConstraint("tenant_id", "provider", "name", name="uq_connection_name"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    name: Mapped[str] = mapped_column(String(120), default="default")
    mode: Mapped[str] = mapped_column(String(10), default="mock")
    environment: Mapped[str] = mapped_column(String(20), default="mock")
    base_url: Mapped[str] = mapped_column(String(300))
    secret_ref: Mapped[str | None] = mapped_column(String(200), nullable=True)
    provider_account_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    config_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="mock", index=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_check_ok: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    last_check_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    tenant = relationship("Tenant")


class IntegrationJob(Base):
    __tablename__ = "integration_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    connection_id: Mapped[int] = mapped_column(ForeignKey("integration_connections.id"), index=True)
    job_type: Mapped[str] = mapped_column(String(80), index=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    schedule: Mapped[str | None] = mapped_column(String(60), nullable=True)


class IntegrationJobRun(Base):
    __tablename__ = "integration_job_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("integration_jobs.id"), index=True)
    status: Mapped[str] = mapped_column(String(30), index=True, default="pending")
    correlation_id: Mapped[str] = mapped_column(String(80), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    records_raw: Mapped[int] = mapped_column(Integer, default=0)
    records_normalized: Mapped[int] = mapped_column(Integer, default=0)


class IntegrationMapping(Base):
    __tablename__ = "integration_mappings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    connection_id: Mapped[int | None] = mapped_column(ForeignKey("integration_connections.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    object_name: Mapped[str] = mapped_column(String(80), index=True)
    version: Mapped[str] = mapped_column(String(20), default="v1")
    mapping_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class IntegrationRawObject(Base):
    __tablename__ = "integration_raw_objects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    job_run_id: Mapped[int] = mapped_column(ForeignKey("integration_job_runs.id"), index=True)
    source_system: Mapped[str] = mapped_column(String(50), index=True)
    endpoint: Mapped[str] = mapped_column(String(120))
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)


class IntegrationError(Base):
    __tablename__ = "integration_errors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    job_run_id: Mapped[int | None] = mapped_column(ForeignKey("integration_job_runs.id"), nullable=True)
    object_name: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[str] = mapped_column(String(20), default="error")
    message: Mapped[str] = mapped_column(Text)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)



class IntegrationSecret(Base):
    __tablename__ = "integration_secrets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    secret_key: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    ciphertext: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(ForeignKey("tenants.id"), nullable=True, index=True)
    actor: Mapped[str] = mapped_column(String(80), default="system")
    action: Mapped[str] = mapped_column(String(80), index=True)
    target_type: Mapped[str] = mapped_column(String(80), index=True)
    target_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    target_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class IntegrationOutboxEvent(Base):
    __tablename__ = "integration_outbox_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80), index=True)
    aggregate_type: Mapped[str] = mapped_column(String(80))
    aggregate_id: Mapped[str] = mapped_column(String(120))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("tenant_id", "external_id", name="uq_product_ext"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80), index=True)
    sku: Mapped[str | None] = mapped_column(String(80), nullable=True)
    name: Mapped[str] = mapped_column(String(250))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification: Mapped[int] = mapped_column(Integer, default=0)
    ledger_account: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cost_center: Mapped[str | None] = mapped_column(String(120), nullable=True)
    allow_decimal: Mapped[bool] = mapped_column(Boolean, default=False)
    stock_control: Mapped[bool] = mapped_column(Boolean, default=False)
    print_detail_pack: Mapped[bool] = mapped_column(Boolean, default=False)
    product_type_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    state: Mapped[int] = mapped_column(Integer, default=0)
    prestashop_product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prestashop_attribute_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    variants = relationship("ProductVariant", cascade="all, delete-orphan", back_populates="product")
    product_taxes = relationship("ProductTax", cascade="all, delete-orphan", back_populates="product")


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (UniqueConstraint("tenant_id", "external_id", name="uq_product_variant_ext"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str | None] = mapped_column(String(250), nullable=True)
    code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    bar_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    unlimited_stock: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_negative_stock: Mapped[bool] = mapped_column(Boolean, default=False)
    state: Mapped[int] = mapped_column(Integer, default=0)
    serial_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prestashop_combination_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    prestashop_value_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    product = relationship("Product", back_populates="variants")


class ProductTax(Base):
    __tablename__ = "product_taxes"
    __table_args__ = (UniqueConstraint("product_id", "tax_external_id", name="uq_product_tax_ref"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80), index=True)
    tax_external_id: Mapped[str] = mapped_column(String(80), index=True)
    product = relationship("Product", back_populates="product_taxes")


class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("tenant_id", "external_id", name="uq_client_ext"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80), index=True)
    first_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    code: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    facebook: Mapped[str | None] = mapped_column(String(200), nullable=True)
    twitter: Mapped[str | None] = mapped_column(String(200), nullable=True)
    has_credit: Mapped[bool] = mapped_column(Boolean, default=False)
    max_credit: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    state: Mapped[int] = mapped_column(Integer, default=0)
    activity: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    municipality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    company_or_person: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points_updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    accumulate_points: Mapped[bool] = mapped_column(Boolean, default=False)
    send_dte: Mapped[bool] = mapped_column(Boolean, default=False)
    prestashop_client_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    office_external_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    contacts = relationship("ClientContact", cascade="all, delete-orphan", back_populates="client")
    addresses = relationship("ClientAddress", cascade="all, delete-orphan", back_populates="client")
    attributes = relationship("ClientAttribute", cascade="all, delete-orphan", back_populates="client")


class ClientContact(Base):
    __tablename__ = "client_contacts"
    __table_args__ = (UniqueConstraint("client_id", "external_id", name="uq_client_contact_ext"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80), index=True)
    first_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    client = relationship("Client", back_populates="contacts")


class ClientAddress(Base):
    __tablename__ = "client_addresses"
    __table_args__ = (UniqueConstraint("client_id", "external_id", name="uq_client_address_ext"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80), index=True)
    address_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    municipality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[int] = mapped_column(Integer, default=0)
    client = relationship("Client", back_populates="addresses")


class ClientAttribute(Base):
    __tablename__ = "client_attributes"
    __table_args__ = (UniqueConstraint("client_id", "external_id", name="uq_client_attribute_ext"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    client = relationship("Client", back_populates="attributes")


class Branch(Base):
    __tablename__ = "branches"
    __table_args__ = (UniqueConstraint("tenant_id", "external_id", name="uq_branch_ext"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    latitude: Mapped[str | None] = mapped_column(String(80), nullable=True)
    longitude: Mapped[str | None] = mapped_column(String(80), nullable=True)
    is_virtual: Mapped[bool] = mapped_column(Boolean, default=False)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True)
    municipality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    cost_center: Mapped[str | None] = mapped_column(String(120), nullable=True)
    state: Mapped[int] = mapped_column(Integer, default=0)
    imagestion_cellar_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code: Mapped[str | None] = mapped_column(String(30), nullable=True)


class DocumentType(Base):
    __tablename__ = "document_types"
    __table_args__ = (UniqueConstraint("tenant_id", "external_id", name="uq_document_type_ext"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(200))
    initial_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code_sii: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    is_electronic_document: Mapped[bool] = mapped_column(Boolean, default=False)
    breakdown_tax: Mapped[bool] = mapped_column(Boolean, default=False)
    use: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_sales_note: Mapped[bool] = mapped_column(Boolean, default=False)
    is_exempt: Mapped[bool] = mapped_column(Boolean, default=False)
    restricts_tax: Mapped[bool] = mapped_column(Boolean, default=False)
    use_client: Mapped[bool] = mapped_column(Boolean, default=False)
    message_body_format: Mapped[str | None] = mapped_column(Text, nullable=True)
    thermal_printer: Mapped[bool] = mapped_column(Boolean, default=False)
    state: Mapped[int] = mapped_column(Integer, default=0)
    copy_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_credit_note: Mapped[bool] = mapped_column(Boolean, default=False)
    continued_high: Mapped[bool] = mapped_column(Boolean, default=False)
    ledger_account: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ipad_print: Mapped[bool] = mapped_column(Boolean, default=False)
    ipad_print_high: Mapped[bool] = mapped_column(Boolean, default=False)
    book_type_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StockSnapshot(Base):
    __tablename__ = "stock_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    product_external_id: Mapped[str] = mapped_column(String(80), index=True)
    branch_external_id: Mapped[str] = mapped_column(String(80), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class SalesDocument(Base):
    __tablename__ = "sales_documents"
    __table_args__ = (UniqueConstraint("tenant_id", "external_id", name="uq_sales_doc_ext"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(80), index=True)
    document_type_id: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    branch_external_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    issued_at: Mapped[datetime] = mapped_column(DateTime)
    customer_external_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    exempt_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    state: Mapped[int] = mapped_column(Integer, default=0)
    lines = relationship("SalesDocumentLine", cascade="all, delete-orphan")


class SalesDocumentLine(Base):
    __tablename__ = "sales_document_lines"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sales_document_id: Mapped[int] = mapped_column(ForeignKey("sales_documents.id"), index=True)
    line_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    variant_external_id: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    variant_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    product_external_id: Mapped[str] = mapped_column(String(80), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 3))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    net_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    tax_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    discount: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=0)
