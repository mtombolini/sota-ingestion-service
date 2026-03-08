"""phase 1 and 2 tenant-aware admin + connection metadata

Revision ID: 0002_phase1_phase2_connections
Revises: 0001_initial_schema
Create Date: 2026-03-08
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_phase1_phase2_connections"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "integration_connections",
        sa.Column("name", sa.String(length=120), nullable=False, server_default="default"),
    )
    op.add_column(
        "integration_connections",
        sa.Column("status", sa.String(length=40), nullable=False, server_default="mock"),
    )
    op.add_column("integration_connections", sa.Column("last_checked_at", sa.DateTime(), nullable=True))
    op.add_column("integration_connections", sa.Column("last_check_ok", sa.Boolean(), nullable=True))
    op.add_column("integration_connections", sa.Column("last_check_message", sa.Text(), nullable=True))
    op.create_index("ix_integration_connections_status", "integration_connections", ["status"])
    op.create_unique_constraint(
        "uq_connection_name",
        "integration_connections",
        ["tenant_id", "provider", "name"],
    )

    op.execute(
        """
        UPDATE integration_connections
        SET name = provider || ' #' || id
        WHERE name = 'default' OR name IS NULL OR name = ''
        """
    )
    op.execute(
        """
        UPDATE integration_connections
        SET status = CASE
            WHEN mode = 'mock' THEN 'mock'
            WHEN base_url IS NULL OR base_url = '' OR secret_ref IS NULL OR secret_ref = '' THEN 'config_incomplete'
            ELSE 'configured'
        END
        """
    )


def downgrade() -> None:
    op.drop_constraint("uq_connection_name", "integration_connections", type_="unique")
    op.drop_index("ix_integration_connections_status", table_name="integration_connections")
    op.drop_column("integration_connections", "last_check_message")
    op.drop_column("integration_connections", "last_check_ok")
    op.drop_column("integration_connections", "last_checked_at")
    op.drop_column("integration_connections", "status")
    op.drop_column("integration_connections", "name")
