"""add client ingestion canonical tables

Revision ID: 0006_clients_ingestion
Revises: 0005_product_catalog_alignment
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_clients_ingestion"
down_revision = "0005_product_catalog_alignment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("external_id", sa.String(length=80), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=True),
        sa.Column("last_name", sa.String(length=120), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("facebook", sa.String(length=200), nullable=True),
        sa.Column("twitter", sa.String(length=200), nullable=True),
        sa.Column("has_credit", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("max_credit", sa.Numeric(14, 2), nullable=True),
        sa.Column("state", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activity", sa.String(length=200), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("municipality", sa.String(length=120), nullable=True),
        sa.Column("address", sa.String(length=300), nullable=True),
        sa.Column("company_or_person", sa.Integer(), nullable=True),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("points_updated_at", sa.DateTime(), nullable=True),
        sa.Column("accumulate_points", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("send_dte", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("prestashop_client_id", sa.String(length=80), nullable=True),
        sa.Column("office_external_id", sa.String(length=80), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "external_id", name="uq_client_ext"),
    )
    op.create_index("ix_clients_tenant_id", "clients", ["tenant_id"])
    op.create_index("ix_clients_external_id", "clients", ["external_id"])
    op.create_index("ix_clients_code", "clients", ["code"])
    op.create_index("ix_clients_office_external_id", "clients", ["office_external_id"])

    op.create_table(
        "client_contacts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("external_id", sa.String(length=80), nullable=False),
        sa.Column("first_name", sa.String(length=120), nullable=True),
        sa.Column("last_name", sa.String(length=120), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.UniqueConstraint("client_id", "external_id", name="uq_client_contact_ext"),
    )
    op.create_index("ix_client_contacts_tenant_id", "client_contacts", ["tenant_id"])
    op.create_index("ix_client_contacts_client_id", "client_contacts", ["client_id"])
    op.create_index("ix_client_contacts_external_id", "client_contacts", ["external_id"])

    op.create_table(
        "client_addresses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("external_id", sa.String(length=80), nullable=False),
        sa.Column("address_name", sa.String(length=120), nullable=True),
        sa.Column("address", sa.String(length=300), nullable=True),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("municipality", sa.String(length=120), nullable=True),
        sa.Column("state", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("client_id", "external_id", name="uq_client_address_ext"),
    )
    op.create_index("ix_client_addresses_tenant_id", "client_addresses", ["tenant_id"])
    op.create_index("ix_client_addresses_client_id", "client_addresses", ["client_id"])
    op.create_index("ix_client_addresses_external_id", "client_addresses", ["external_id"])

    op.create_table(
        "client_attributes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=False),
        sa.Column("external_id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("value", sa.Text(), nullable=True),
        sa.UniqueConstraint("client_id", "external_id", name="uq_client_attribute_ext"),
    )
    op.create_index("ix_client_attributes_tenant_id", "client_attributes", ["tenant_id"])
    op.create_index("ix_client_attributes_client_id", "client_attributes", ["client_id"])
    op.create_index("ix_client_attributes_external_id", "client_attributes", ["external_id"])


def downgrade() -> None:
    op.drop_index("ix_client_attributes_external_id", table_name="client_attributes")
    op.drop_index("ix_client_attributes_client_id", table_name="client_attributes")
    op.drop_index("ix_client_attributes_tenant_id", table_name="client_attributes")
    op.drop_table("client_attributes")

    op.drop_index("ix_client_addresses_external_id", table_name="client_addresses")
    op.drop_index("ix_client_addresses_client_id", table_name="client_addresses")
    op.drop_index("ix_client_addresses_tenant_id", table_name="client_addresses")
    op.drop_table("client_addresses")

    op.drop_index("ix_client_contacts_external_id", table_name="client_contacts")
    op.drop_index("ix_client_contacts_client_id", table_name="client_contacts")
    op.drop_index("ix_client_contacts_tenant_id", table_name="client_contacts")
    op.drop_table("client_contacts")

    op.drop_index("ix_clients_office_external_id", table_name="clients")
    op.drop_index("ix_clients_code", table_name="clients")
    op.drop_index("ix_clients_external_id", table_name="clients")
    op.drop_index("ix_clients_tenant_id", table_name="clients")
    op.drop_table("clients")
