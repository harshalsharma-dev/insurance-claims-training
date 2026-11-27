"""create users policies and claims tables

Revision ID: 64492906136c
Revises:
Create Date: 2026-11-16 13:43:43.331824

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "64492906136c"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("role", sa.String(length=30), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("refresh_token_hash", sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_user_id", "users", ["user_id"], unique=False)

    op.create_table(
        "policies",
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("policy_number", sa.String(length=20), nullable=False),
        sa.Column("policy_type", sa.String(length=30), nullable=False),
        sa.PrimaryKeyConstraint("policy_id"),
    )
    op.create_index("ix_policies_policy_id", "policies", ["policy_id"])
    op.create_index(
        "ix_policies_policy_number",
        "policies",
        ["policy_number"],
        unique=True,
    )

    op.create_table(
        "user_policies",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["policy_id"], ["policies.policy_id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("user_id", "policy_id"),
    )

    op.create_table(
        "claims",
        sa.Column("claim_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("policy_id", sa.Integer(), nullable=False),
        sa.Column("claim_type", sa.String(length=30), nullable=False),
        sa.Column("claim_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.ForeignKeyConstraint(["policy_id"], ["policies.policy_id"]),
        sa.PrimaryKeyConstraint("claim_id"),
    )
    op.create_index("ix_claims_claim_id", "claims", ["claim_id"])
    op.create_index("ix_claims_user_id", "claims", ["user_id"])
    op.create_index("ix_claims_policy_id", "claims", ["policy_id"])


def downgrade() -> None:
    op.drop_index("ix_claims_policy_id", table_name="claims")
    op.drop_index("ix_claims_user_id", table_name="claims")
    op.drop_index("ix_claims_claim_id", table_name="claims")
    op.drop_table("claims")

    op.drop_table("user_policies")

    op.drop_index("ix_policies_policy_number", table_name="policies")
    op.drop_index("ix_policies_policy_id", table_name="policies")
    op.drop_table("policies")

    op.drop_index("ix_users_user_id", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
