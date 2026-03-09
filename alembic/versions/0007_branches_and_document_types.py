"""align branches with Bsale offices and add document types

Revision ID: 0007_branches_and_document_types
Revises: 0006_clients_ingestion
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_branches_and_document_types"
down_revision = "0006_clients_ingestion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("branches", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("branches", sa.Column("address", sa.String(length=300), nullable=True))
    op.add_column("branches", sa.Column("latitude", sa.String(length=80), nullable=True))
    op.add_column("branches", sa.Column("longitude", sa.String(length=80), nullable=True))
    op.add_column("branches", sa.Column("is_virtual", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("branches", sa.Column("country", sa.String(length=120), nullable=True))
    op.add_column("branches", sa.Column("municipality", sa.String(length=120), nullable=True))
    op.add_column("branches", sa.Column("city", sa.String(length=120), nullable=True))
    op.add_column("branches", sa.Column("zip_code", sa.String(length=40), nullable=True))
    op.add_column("branches", sa.Column("cost_center", sa.String(length=120), nullable=True))
    op.add_column("branches", sa.Column("state", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("branches", sa.Column("imagestion_cellar_id", sa.Integer(), nullable=True))

    op.create_table(
        "document_types",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("external_id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("initial_number", sa.Integer(), nullable=True),
        sa.Column("code_sii", sa.String(length=40), nullable=True),
        sa.Column("is_electronic_document", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("breakdown_tax", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("use", sa.Integer(), nullable=True),
        sa.Column("is_sales_note", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_exempt", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("restricts_tax", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("use_client", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("message_body_format", sa.Text(), nullable=True),
        sa.Column("thermal_printer", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("state", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("copy_number", sa.Integer(), nullable=True),
        sa.Column("is_credit_note", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("continued_high", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("ledger_account", sa.String(length=120), nullable=True),
        sa.Column("ipad_print", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("ipad_print_high", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("book_type_id", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("tenant_id", "external_id", name="uq_document_type_ext"),
    )
    op.create_index("ix_document_types_tenant_id", "document_types", ["tenant_id"])
    op.create_index("ix_document_types_external_id", "document_types", ["external_id"])
    op.create_index("ix_document_types_code_sii", "document_types", ["code_sii"])
    op.create_index("ix_document_types_book_type_id", "document_types", ["book_type_id"])


def downgrade() -> None:
    op.drop_index("ix_document_types_book_type_id", table_name="document_types")
    op.drop_index("ix_document_types_code_sii", table_name="document_types")
    op.drop_index("ix_document_types_external_id", table_name="document_types")
    op.drop_index("ix_document_types_tenant_id", table_name="document_types")
    op.drop_table("document_types")

    op.drop_column("branches", "imagestion_cellar_id")
    op.drop_column("branches", "state")
    op.drop_column("branches", "cost_center")
    op.drop_column("branches", "zip_code")
    op.drop_column("branches", "city")
    op.drop_column("branches", "municipality")
    op.drop_column("branches", "country")
    op.drop_column("branches", "is_virtual")
    op.drop_column("branches", "longitude")
    op.drop_column("branches", "latitude")
    op.drop_column("branches", "address")
    op.drop_column("branches", "description")
