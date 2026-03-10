"""Replace ERP-specific models with canonical data model v2

Drop Bsale-specific tables (products, product_variants, product_taxes,
clients, client_contacts, client_addresses, client_attributes, branches,
document_types, stock_snapshots, sales_documents, sales_document_lines)
and create canonical tables (categories, products, suppliers,
supplier_products, locations, stock, stock_movements, sales_orders,
sales_order_lines, purchase_orders, purchase_order_lines,
transfer_orders, transfer_lines).

Revision ID: 0008_canonical_model_v2
Revises: 0007_branches_and_document_types
Create Date: 2026-03-09
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_canonical_model_v2"
down_revision = "0007_branches_and_document_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Drop old Bsale-specific tables (FK-safe order) ---
    op.drop_table("sales_document_lines")
    op.drop_table("sales_documents")
    op.drop_table("stock_snapshots")
    op.drop_table("client_attributes")
    op.drop_table("client_addresses")
    op.drop_table("client_contacts")
    op.drop_table("clients")
    op.drop_table("product_taxes")
    op.drop_table("product_variants")
    op.drop_table("products")
    op.drop_table("document_types")
    op.drop_table("branches")

    # --- Create canonical Layer 1: Master Data ---
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(80), index=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("parent_category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "source_system", "external_id", name="uq_category_ext"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(80), index=True, nullable=False),
        sa.Column("sku", sa.String(80), nullable=True, index=True),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id"), nullable=True, index=True),
        sa.Column("brand", sa.String(120), nullable=True),
        sa.Column("unit_of_measure", sa.String(20), nullable=True),
        sa.Column("unit_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("weight_kg", sa.Numeric(10, 4), nullable=True),
        sa.Column("volume_m3", sa.Numeric(10, 6), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("min_order_qty", sa.Numeric(14, 3), nullable=True),
        sa.Column("shelf_life_days", sa.Integer(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "source_system", "external_id", name="uq_product_ext"),
    )

    op.create_table(
        "variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(80), index=True, nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), nullable=True, index=True),
        sa.Column("product_external_id", sa.String(80), nullable=True, index=True),
        sa.Column("sku", sa.String(80), nullable=True, index=True),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("barcode", sa.String(80), nullable=True, index=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("allows_negative_stock", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("unlimited_stock", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "source_system", "external_id", name="uq_variant_ext"),
    )

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(80), index=True, nullable=False),
        sa.Column("tax_id", sa.String(80), nullable=True),
        sa.Column("name", sa.String(250), nullable=False),
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column("contact_email", sa.String(200), nullable=True),
        sa.Column("contact_phone", sa.String(80), nullable=True),
        sa.Column("payment_terms_days", sa.Integer(), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "source_system", "external_id", name="uq_supplier_ext"),
    )

    op.create_table(
        "supplier_products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(80), index=True, nullable=False),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id"), index=True, nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id"), index=True, nullable=False),
        sa.Column("supplier_sku", sa.String(80), nullable=True),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("lead_time_days", sa.Integer(), nullable=True),
        sa.Column("min_order_qty", sa.Numeric(14, 3), nullable=True),
        sa.Column("is_preferred", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("supplier_id", "product_id", name="uq_supplier_product"),
    )

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(80), index=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("type", sa.String(20), nullable=False, server_default="STORE"),
        sa.Column("address", sa.String(300), nullable=True),
        sa.Column("city", sa.String(120), nullable=True),
        sa.Column("region", sa.String(120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("parent_location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "source_system", "external_id", name="uq_location_ext"),
    )

    # --- Create canonical Layer 2: Inventory ---
    op.create_table(
        "stock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(120), index=True, nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("variants.id"), nullable=True, index=True),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True, index=True),
        sa.Column("variant_external_id", sa.String(80), index=True, nullable=False),
        sa.Column("location_external_id", sa.String(80), index=True, nullable=False),
        sa.Column("quantity_on_hand", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("quantity_reserved", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("quantity_available", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("quantity_in_transit", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("last_updated", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "source_system", "variant_external_id", "location_external_id", name="uq_stock_variant_location"),
    )

    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(80), index=True, nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("variants.id"), nullable=True, index=True),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True, index=True),
        sa.Column("variant_external_id", sa.String(80), index=True, nullable=False),
        sa.Column("location_external_id", sa.String(80), nullable=True, index=True),
        sa.Column("movement_type", sa.String(20), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("reference_type", sa.String(20), nullable=True),
        sa.Column("reference_id", sa.String(80), nullable=True),
        sa.Column("movement_date", sa.DateTime(), nullable=False),
        sa.Column("unit_cost", sa.Numeric(14, 2), nullable=True),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "source_system", "external_id", name="uq_stock_movement_ext"),
    )

    # --- Create canonical Layer 3: Demand / Sales ---
    op.create_table(
        "sales_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(80), index=True, nullable=False),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True, index=True),
        sa.Column("location_external_id", sa.String(80), nullable=True),
        sa.Column("order_date", sa.DateTime(), nullable=False),
        sa.Column("customer_ref", sa.String(120), nullable=True),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("channel", sa.String(40), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="CONFIRMED"),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "source_system", "external_id", name="uq_sales_order_ext"),
    )

    op.create_table(
        "sales_order_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sales_order_id", sa.Integer(), sa.ForeignKey("sales_orders.id"), index=True, nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("variants.id"), nullable=True, index=True),
        sa.Column("variant_external_id", sa.String(80), index=True, nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("discount_pct", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # --- Create canonical Layer 4: Purchasing & Transfers ---
    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(80), index=True, nullable=False),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("suppliers.id"), nullable=True, index=True),
        sa.Column("location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True, index=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("order_date", sa.Date(), nullable=True),
        sa.Column("expected_delivery", sa.Date(), nullable=True),
        sa.Column("actual_delivery", sa.Date(), nullable=True),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=True),
        sa.Column("currency", sa.String(10), nullable=True),
        sa.Column("created_by", sa.String(80), nullable=True),
        sa.Column("approved_by", sa.String(80), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "source_system", "external_id", name="uq_purchase_order_ext"),
    )

    op.create_table(
        "purchase_order_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("purchase_order_id", sa.Integer(), sa.ForeignKey("purchase_orders.id"), index=True, nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("variants.id"), nullable=True, index=True),
        sa.Column("variant_external_id", sa.String(80), index=True, nullable=False),
        sa.Column("quantity_ordered", sa.Numeric(14, 3), nullable=False),
        sa.Column("quantity_received", sa.Numeric(14, 3), nullable=False, server_default="0"),
        sa.Column("unit_price", sa.Numeric(14, 2), nullable=False),
        sa.Column("discount_pct", sa.Numeric(8, 2), nullable=False, server_default="0"),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        "transfer_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), index=True, nullable=False),
        sa.Column("source_system", sa.String(50), index=True, nullable=False),
        sa.Column("external_id", sa.String(80), index=True, nullable=False),
        sa.Column("from_location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("to_location_id", sa.Integer(), sa.ForeignKey("locations.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("created_date", sa.Date(), nullable=True),
        sa.Column("shipped_date", sa.Date(), nullable=True),
        sa.Column("received_date", sa.Date(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "source_system", "external_id", name="uq_transfer_order_ext"),
    )

    op.create_table(
        "transfer_lines",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transfer_id", sa.Integer(), sa.ForeignKey("transfer_orders.id"), index=True, nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("variants.id"), nullable=True, index=True),
        sa.Column("variant_external_id", sa.String(80), index=True, nullable=False),
        sa.Column("quantity", sa.Numeric(14, 3), nullable=False),
        sa.Column("ingested_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    # Drop canonical tables
    op.drop_table("transfer_lines")
    op.drop_table("transfer_orders")
    op.drop_table("purchase_order_lines")
    op.drop_table("purchase_orders")
    op.drop_table("sales_order_lines")
    op.drop_table("sales_orders")
    op.drop_table("stock_movements")
    op.drop_table("stock")
    op.drop_table("variants")
    op.drop_table("locations")
    op.drop_table("supplier_products")
    op.drop_table("suppliers")
    op.drop_table("products")
    op.drop_table("categories")
    # Note: downgrade does not recreate the old Bsale-specific tables.
    # A full rollback requires restoring from backup.
