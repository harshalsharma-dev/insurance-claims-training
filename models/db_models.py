from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Table,
    func,
)
from sqlalchemy.orm import relationship

from database import Base

# Association table: many users can have many policies
user_policies = Table(
    "user_policies",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "policy_id",
        Integer,
        ForeignKey("policies.policy_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# User ORM Model
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=True)
    role = Column(String(30), nullable=False, default="claimant")

    password_hash = Column(String(255), nullable=True)
    refresh_token_hash = Column(String(255), nullable=True)

    policies = relationship(
        "Policy",
        secondary=user_policies,
        back_populates="users",
    )

    claims = relationship("Claim", back_populates="user")


# Policy ORM Model
class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(Integer, primary_key=True, index=True)
    policy_number = Column(String(20), unique=True, nullable=False, index=True)
    policy_type = Column(String(30), nullable=False)

    users = relationship(
        "User",
        secondary=user_policies,
        back_populates="policies",
    )

    claims = relationship("Claim", back_populates="policy")


# Claim ORM Model
class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    policy_id = Column(
        Integer,
        ForeignKey("policies.policy_id"),
        nullable=False,
        index=True,
    )

    claim_type = Column(String(30), nullable=False)
    claim_amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(20), nullable=False, default="Submitted")
    priority = Column(String(20), nullable=False, default="Medium")
    description = Column(String, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="claims")
    policy = relationship("Policy", back_populates="claims")
