"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-03-07
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("tenants", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("slug", sa.String(80), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.create_table("integration_connections", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("provider", sa.String(50), nullable=False), sa.Column("mode", sa.String(10), nullable=False), sa.Column("base_url", sa.String(300), nullable=False), sa.Column("secret_ref", sa.String(200)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.create_index("ix_integration_connections_provider", "integration_connections", ["provider"])

    op.create_table("integration_jobs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("connection_id", sa.Integer(), sa.ForeignKey("integration_connections.id"), nullable=False), sa.Column("job_type", sa.String(80), nullable=False), sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.Column("schedule", sa.String(60)))
    op.create_index("ix_integration_jobs_job_type", "integration_jobs", ["job_type"])

    op.create_table("integration_job_runs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("job_id", sa.Integer(), sa.ForeignKey("integration_jobs.id"), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("correlation_id", sa.String(80), nullable=False), sa.Column("started_at", sa.DateTime(), nullable=False), sa.Column("finished_at", sa.DateTime()), sa.Column("records_raw", sa.Integer(), nullable=False, server_default="0"), sa.Column("records_normalized", sa.Integer(), nullable=False, server_default="0"))

    op.create_table("integration_mappings", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("provider", sa.String(50), nullable=False), sa.Column("object_name", sa.String(80), nullable=False), sa.Column("version", sa.String(20), nullable=False), sa.Column("mapping_payload", sa.JSON(), nullable=False), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.create_table("integration_raw_objects", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("job_run_id", sa.Integer(), sa.ForeignKey("integration_job_runs.id"), nullable=False), sa.Column("source_system", sa.String(50), nullable=False), sa.Column("endpoint", sa.String(120), nullable=False), sa.Column("checksum", sa.String(64), nullable=False), sa.Column("fetched_at", sa.DateTime(), nullable=False), sa.Column("payload", sa.JSON(), nullable=False))
    op.create_table("integration_errors", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("job_run_id", sa.Integer(), sa.ForeignKey("integration_job_runs.id")), sa.Column("object_name", sa.String(80), nullable=False), sa.Column("severity", sa.String(20), nullable=False), sa.Column("message", sa.Text(), nullable=False), sa.Column("payload", sa.JSON()), sa.Column("created_at", sa.DateTime(), nullable=False))
    op.create_table("integration_watermarks", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("provider", sa.String(50), nullable=False), sa.Column("object_name", sa.String(80), nullable=False), sa.Column("last_cursor", sa.String(120)), sa.Column("last_synced_at", sa.DateTime()), sa.UniqueConstraint("tenant_id", "provider", "object_name", name="uq_wm_scope"))
    op.create_table("integration_outbox_events", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("event_type", sa.String(80), nullable=False), sa.Column("aggregate_type", sa.String(80), nullable=False), sa.Column("aggregate_id", sa.String(120), nullable=False), sa.Column("payload", sa.JSON(), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(), nullable=False))

    op.create_table("products", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("external_id", sa.String(80), nullable=False), sa.Column("sku", sa.String(80)), sa.Column("name", sa.String(250), nullable=False), sa.Column("category", sa.String(120)), sa.Column("unit", sa.String(20)), sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")), sa.UniqueConstraint("tenant_id", "external_id", name="uq_product_ext"))
    op.create_table("branches", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("external_id", sa.String(80), nullable=False), sa.Column("name", sa.String(200), nullable=False), sa.Column("code", sa.String(30)), sa.UniqueConstraint("tenant_id", "external_id", name="uq_branch_ext"))
    op.create_table("stock_snapshots", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("product_external_id", sa.String(80), nullable=False), sa.Column("branch_external_id", sa.String(80), nullable=False), sa.Column("quantity", sa.Numeric(14, 3), nullable=False), sa.Column("captured_at", sa.DateTime(), nullable=False))
    op.create_table("sales_documents", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False), sa.Column("external_id", sa.String(80), nullable=False), sa.Column("branch_external_id", sa.String(80)), sa.Column("issued_at", sa.DateTime(), nullable=False), sa.Column("customer_external_id", sa.String(80)), sa.Column("total_amount", sa.Numeric(14, 2), nullable=False), sa.UniqueConstraint("tenant_id", "external_id", name="uq_sales_doc_ext"))
    op.create_table("sales_document_lines", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("sales_document_id", sa.Integer(), sa.ForeignKey("sales_documents.id"), nullable=False), sa.Column("product_external_id", sa.String(80), nullable=False), sa.Column("quantity", sa.Numeric(14, 3), nullable=False), sa.Column("unit_price", sa.Numeric(14, 2), nullable=False))


def downgrade() -> None:
    for table in [
        "sales_document_lines", "sales_documents", "stock_snapshots", "branches", "products", "integration_outbox_events", "integration_watermarks", "integration_errors", "integration_raw_objects", "integration_mappings", "integration_job_runs", "integration_jobs", "integration_connections", "tenants",
    ]:
        op.drop_table(table)
