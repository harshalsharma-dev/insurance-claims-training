"""create default admin user

Revision ID: 2a60a8c98968
Revises: 64492906136c
Create Date: 2026-11-21 06:29:03.514834

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "2a60a8c98968"
down_revision: Union[str, Sequence[str], None] = "64492906136c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade():
    connection = op.get_bind()

    users = sa.table(
        "users",
        sa.column("user_id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("email", sa.String),
        sa.column("phone_number", sa.String),
        sa.column("role", sa.String),
        sa.column("password_hash", sa.String),
        sa.column("refresh_token_hash", sa.String),
    )

    admin = (
        connection.execute(sa.select(users).where(users.c.email == "admin@gmail.com"))
        .mappings()
        .first()
    )

    if admin is None:
        connection.execute(
            users.insert().values(
                name="Insurance Admin",
                email="admin@gmail.com",
                phone_number=None,
                role="admin",
                password_hash=pwd_context.hash("pass-admin@123"),
                refresh_token_hash=None,
            )
        )
    else:
        connection.execute(
            users.update()
            .where(users.c.email == "admin@gmail.com")
            .values(role="admin")
        )


def downgrade():
    connection = op.get_bind()

    connection.execute(sa.text("""
            DELETE FROM users
            WHERE email = 'admin@gmail.com'
        """))
