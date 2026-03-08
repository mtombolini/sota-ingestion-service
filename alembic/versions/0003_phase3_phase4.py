"""phase 3 and 4 provider registry, secret storage and audit

Revision ID: 0003_phase3_phase4
Revises: 0002_phase1_phase2_connections
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_phase3_phase4"
down_revision = "0002_phase1_phase2_connections"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "integration_connections",
        sa.Column("environment", sa.String(length=20), nullable=False, server_default="mock"),
    )
    op.add_column(
        "integration_connections",
        sa.Column("provider_account_id", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "integration_connections",
        sa.Column("config_payload", sa.JSON(), nullable=True),
    )
    op.add_column(
        "integration_connections",
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "integration_connections",
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
    )
    op.create_index("ix_integration_connections_environment", "integration_connections", ["environment"])
    op.create_index("ix_integration_connections_is_primary", "integration_connections", ["is_primary"])

    op.add_column(
        "integration_mappings",
        sa.Column("connection_id", sa.Integer(), sa.ForeignKey("integration_connections.id"), nullable=True),
    )
    op.create_index("ix_integration_mappings_connection_id", "integration_mappings", ["connection_id"])

    op.create_table(
        "integration_secrets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("provider", sa.String(length=50), nullable=True),
        sa.Column("secret_key", sa.String(length=80), nullable=False),
        sa.Column("ciphertext", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_integration_secrets_secret_key", "integration_secrets", ["secret_key"], unique=True)
    op.create_index("ix_integration_secrets_tenant_id", "integration_secrets", ["tenant_id"])
    op.create_index("ix_integration_secrets_provider", "integration_secrets", ["provider"])

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("tenant_id", sa.Integer(), sa.ForeignKey("tenants.id"), nullable=True),
        sa.Column("actor", sa.String(length=80), nullable=False, server_default="system"),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("target_type", sa.String(length=80), nullable=False),
        sa.Column("target_id", sa.String(length=120), nullable=True),
        sa.Column("target_label", sa.String(length=200), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_admin_audit_logs_tenant_id", "admin_audit_logs", ["tenant_id"])
    op.create_index("ix_admin_audit_logs_action", "admin_audit_logs", ["action"])
    op.create_index("ix_admin_audit_logs_target_type", "admin_audit_logs", ["target_type"])

    op.execute(
        """
        UPDATE integration_connections
        SET environment = CASE
            WHEN mode = 'mock' THEN 'mock'
            ELSE 'production'
        END,
            is_primary = true,
            priority = 100
        WHERE id IN (
            SELECT ranked.id
            FROM (
                SELECT id,
                       ROW_NUMBER() OVER (PARTITION BY tenant_id, provider ORDER BY id) AS row_num
                FROM integration_connections
            ) AS ranked
            WHERE ranked.row_num = 1
        )
        """
    )
    op.execute(
        """
        UPDATE integration_connections
        SET environment = CASE
            WHEN mode = 'mock' THEN 'mock'
            ELSE 'production'
        END,
            is_primary = COALESCE(is_primary, false),
            priority = COALESCE(priority, 100)
        WHERE environment IS NULL OR environment = ''
        """
    )


def downgrade() -> None:
    op.drop_index("ix_admin_audit_logs_target_type", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_action", table_name="admin_audit_logs")
    op.drop_index("ix_admin_audit_logs_tenant_id", table_name="admin_audit_logs")
    op.drop_table("admin_audit_logs")

    op.drop_index("ix_integration_secrets_provider", table_name="integration_secrets")
    op.drop_index("ix_integration_secrets_tenant_id", table_name="integration_secrets")
    op.drop_index("ix_integration_secrets_secret_key", table_name="integration_secrets")
    op.drop_table("integration_secrets")

    op.drop_index("ix_integration_mappings_connection_id", table_name="integration_mappings")
    op.drop_column("integration_mappings", "connection_id")

    op.drop_index("ix_integration_connections_is_primary", table_name="integration_connections")
    op.drop_index("ix_integration_connections_environment", table_name="integration_connections")
    op.drop_column("integration_connections", "priority")
    op.drop_column("integration_connections", "is_primary")
    op.drop_column("integration_connections", "config_payload")
    op.drop_column("integration_connections", "provider_account_id")
    op.drop_column("integration_connections", "environment")
