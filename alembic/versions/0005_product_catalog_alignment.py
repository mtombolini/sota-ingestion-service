"""product catalog alignment for real bsale api

Revision ID: 0005_product_catalog_alignment
Revises: 0004_documents_enrich
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_product_catalog_alignment"
down_revision = "0004_documents_enrich"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("classification", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("products", sa.Column("ledger_account", sa.String(length=120), nullable=True))
    op.add_column("products", sa.Column("cost_center", sa.String(length=120), nullable=True))
    op.add_column("products", sa.Column("allow_decimal", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("products", sa.Column("stock_control", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("products", sa.Column("print_detail_pack", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("products", sa.Column("product_type_id", sa.String(length=20), nullable=True))
    op.add_column("products", sa.Column("state", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("products", sa.Column("prestashop_product_id", sa.Integer(), nullable=True))
    op.add_column("products", sa.Column("prestashop_attribute_id", sa.Integer(), nullable=True))
    op.create_index("ix_products_product_type_id", "products", ["product_type_id"])

    op.execute(
        """
        UPDATE products
        SET state = CASE
            WHEN is_active THEN 0
            ELSE 1
        END
        """
    )

    op.create_table(
        "product_variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("external_id", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=250), nullable=True),
        sa.Column("code", sa.String(length=80), nullable=True),
        sa.Column("bar_code", sa.String(length=80), nullable=True),
        sa.Column("unlimited_stock", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("allow_negative_stock", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("state", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("serial_number", sa.Integer(), nullable=True),
        sa.Column("prestashop_combination_id", sa.Integer(), nullable=True),
        sa.Column("prestashop_value_id", sa.Integer(), nullable=True),
        sa.UniqueConstraint("tenant_id", "external_id", name="uq_product_variant_ext"),
    )
    op.create_index("ix_product_variants_tenant_id", "product_variants", ["tenant_id"])
    op.create_index("ix_product_variants_product_id", "product_variants", ["product_id"])
    op.create_index("ix_product_variants_external_id", "product_variants", ["external_id"])
    op.create_index("ix_product_variants_code", "product_variants", ["code"])

    op.create_table(
        "product_taxes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=False),
        sa.Column("external_id", sa.String(length=80), nullable=False),
        sa.Column("tax_external_id", sa.String(length=80), nullable=False),
        sa.UniqueConstraint("product_id", "tax_external_id", name="uq_product_tax_ref"),
    )
    op.create_index("ix_product_taxes_tenant_id", "product_taxes", ["tenant_id"])
    op.create_index("ix_product_taxes_product_id", "product_taxes", ["product_id"])
    op.create_index("ix_product_taxes_external_id", "product_taxes", ["external_id"])
    op.create_index("ix_product_taxes_tax_external_id", "product_taxes", ["tax_external_id"])


def downgrade() -> None:
    op.drop_index("ix_product_taxes_tax_external_id", table_name="product_taxes")
    op.drop_index("ix_product_taxes_external_id", table_name="product_taxes")
    op.drop_index("ix_product_taxes_product_id", table_name="product_taxes")
    op.drop_index("ix_product_taxes_tenant_id", table_name="product_taxes")
    op.drop_table("product_taxes")

    op.drop_index("ix_product_variants_code", table_name="product_variants")
    op.drop_index("ix_product_variants_external_id", table_name="product_variants")
    op.drop_index("ix_product_variants_product_id", table_name="product_variants")
    op.drop_index("ix_product_variants_tenant_id", table_name="product_variants")
    op.drop_table("product_variants")

    op.drop_index("ix_products_product_type_id", table_name="products")
    op.drop_column("products", "prestashop_attribute_id")
    op.drop_column("products", "prestashop_product_id")
    op.drop_column("products", "state")
    op.drop_column("products", "product_type_id")
    op.drop_column("products", "print_detail_pack")
    op.drop_column("products", "stock_control")
    op.drop_column("products", "allow_decimal")
    op.drop_column("products", "cost_center")
    op.drop_column("products", "ledger_account")
    op.drop_column("products", "classification")
    op.drop_column("products", "description")
