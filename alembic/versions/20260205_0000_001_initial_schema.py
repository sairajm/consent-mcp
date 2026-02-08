"""Initial schema for consent_requests table.

Revision ID: 001
Revises:
Create Date: 2026-02-05

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create enums
    contact_type_enum = sa.Enum("phone", "email", name="contact_type_enum")
    consent_status_enum = sa.Enum(
        "pending", "granted", "revoked", "expired", name="consent_status_enum"
    )

    contact_type_enum.create(op.get_bind(), checkfirst=True)
    consent_status_enum.create(op.get_bind(), checkfirst=True)

    # Create consent_requests table
    op.create_table(
        "consent_requests",
        # Primary key
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        # Requester information
        sa.Column("requester_contact_type", contact_type_enum, nullable=False),
        sa.Column("requester_contact_value", sa.String(255), nullable=False),
        sa.Column("requester_name", sa.String(255), nullable=False),
        # Target information
        sa.Column("target_contact_type", contact_type_enum, nullable=False),
        sa.Column("target_contact_value", sa.String(255), nullable=False),
        sa.Column("target_name", sa.String(255), nullable=True),
        # Consent details
        sa.Column("scope", sa.Text, nullable=False),
        sa.Column(
            "status",
            consent_status_enum,
            nullable=False,
            server_default="pending",
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # Audit timestamps
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index(
        "ix_consent_target_lookup",
        "consent_requests",
        ["target_contact_type", "target_contact_value"],
    )
    op.create_index(
        "ix_consent_requester_lookup",
        "consent_requests",
        ["requester_contact_type", "requester_contact_value"],
    )
    op.create_index(
        "ix_consent_status",
        "consent_requests",
        ["status", "expires_at"],
    )

    # Create unique constraint
    op.create_unique_constraint(
        "uq_consent_requester_target_scope",
        "consent_requests",
        [
            "requester_contact_type",
            "requester_contact_value",
            "target_contact_type",
            "target_contact_value",
            "scope",
        ],
    )


def downgrade() -> None:
    # Drop table (cascades to indexes and constraints)
    op.drop_table("consent_requests")

    # Drop enums
    sa.Enum(name="consent_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="contact_type_enum").drop(op.get_bind(), checkfirst=True)
