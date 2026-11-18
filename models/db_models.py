from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    DateTime,
    func,
)
from sqlalchemy.orm import relationship

from database import Base


# User ORM Model
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone_number = Column(String(20), nullable=True)
    role = Column(String(30), nullable=False, default="claimant")

    policies = relationship("Policy", back_populates="owner")


# Policy ORM Model
class Policy(Base):
    __tablename__ = "policies"

    policy_id = Column(Integer, primary_key=True, index=True)
    policy_number = Column(String(20), unique=True, nullable=False, index=True)
    policy_type = Column(String(30), nullable=False)

    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    owner = relationship("User", back_populates="policies")
    claims = relationship("Claim", back_populates="policy")


# Claim ORM Model
class Claim(Base):
    __tablename__ = "claims"

    claim_id = Column(Integer, primary_key=True, index=True)

    policy_id = Column(Integer, ForeignKey("policies.policy_id"), nullable=False)

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

    policy = relationship("Policy", back_populates="claims")
