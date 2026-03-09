"""enrich sales_documents and sales_document_lines with full Bsale fields

Revision ID: 0004_documents_enrich
Revises: 0003_phase3_phase4
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_documents_enrich"
down_revision = "0003_phase3_phase4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # sales_documents: new columns
    op.add_column("sales_documents", sa.Column("document_type_id", sa.String(20), nullable=True))
    op.add_column("sales_documents", sa.Column("number", sa.Integer(), nullable=True))
    op.add_column("sales_documents", sa.Column("net_amount", sa.Numeric(14, 2), nullable=True))
    op.add_column("sales_documents", sa.Column("tax_amount", sa.Numeric(14, 2), nullable=True))
    op.add_column("sales_documents", sa.Column("exempt_amount", sa.Numeric(14, 2), nullable=True))
    op.add_column("sales_documents", sa.Column("state", sa.Integer(), server_default="0", nullable=False))
    op.create_index("ix_sales_documents_document_type_id", "sales_documents", ["document_type_id"])

    # sales_document_lines: new columns
    op.add_column("sales_document_lines", sa.Column("line_number", sa.Integer(), nullable=True))
    op.add_column("sales_document_lines", sa.Column("variant_external_id", sa.String(80), nullable=True))
    op.add_column("sales_document_lines", sa.Column("variant_code", sa.String(80), nullable=True))
    op.add_column("sales_document_lines", sa.Column("net_amount", sa.Numeric(14, 2), nullable=True))
    op.add_column("sales_document_lines", sa.Column("tax_amount", sa.Numeric(14, 2), nullable=True))
    op.add_column("sales_document_lines", sa.Column("total_amount", sa.Numeric(14, 2), nullable=True))
    op.add_column("sales_document_lines", sa.Column("discount", sa.Numeric(8, 2), server_default="0", nullable=False))
    op.create_index("ix_sales_document_lines_variant_external_id", "sales_document_lines", ["variant_external_id"])


def downgrade() -> None:
    op.drop_index("ix_sales_document_lines_variant_external_id", "sales_document_lines")
    op.drop_column("sales_document_lines", "discount")
    op.drop_column("sales_document_lines", "total_amount")
    op.drop_column("sales_document_lines", "tax_amount")
    op.drop_column("sales_document_lines", "net_amount")
    op.drop_column("sales_document_lines", "variant_code")
    op.drop_column("sales_document_lines", "variant_external_id")
    op.drop_column("sales_document_lines", "line_number")

    op.drop_index("ix_sales_documents_document_type_id", "sales_documents")
    op.drop_column("sales_documents", "state")
    op.drop_column("sales_documents", "exempt_amount")
    op.drop_column("sales_documents", "tax_amount")
    op.drop_column("sales_documents", "net_amount")
    op.drop_column("sales_documents", "number")
    op.drop_column("sales_documents", "document_type_id")
