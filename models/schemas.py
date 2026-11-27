from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# Claim creation
class CreateClaim(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    claim_amount: Decimal = Field(gt=0, lt=100000)
    description: str | None = None


class ClaimCreate(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    claim_amount: Decimal = Field(gt=0, lt=100000)
    priority: Literal["Low", "Medium", "High"] = "Medium"
    description: str | None = None


# Full claim update
class UpdateClaim(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    status: Literal["Submitted", "Under Review", "Approved", "Rejected", "Settled"]
    claim_amount: Decimal = Field(gt=0, lt=100000)
    description: str | None = None


class ClaimUpdate(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    status: Literal["Submitted", "Under Review", "Approved", "Rejected", "Settled"]
    priority: Literal["Low", "Medium", "High"]
    claim_amount: Decimal = Field(gt=0, lt=100000)
    description: str | None = None


# Partial claim update
class ClaimPatch(BaseModel):
    claim_amount: Decimal | None = Field(default=None, gt=0, lt=100000)
    status: Literal["Submitted", "Under Review", "Approved", "Rejected", "Settled"] | None = None
    priority: Literal["Low", "Medium", "High"] | None = None
    description: str | None = None


# Claim responses
class CreateClaimDetailResponse(BaseModel):
    policy_number: str
    claim_type: str
    claim_amount: Decimal


class CreateClaimResponse(BaseModel):
    message: str
    claim: CreateClaimDetailResponse


class ClaimsResponse(BaseModel):
    claim_id: int
    policy_number: str
    claim_type: str
    claim_amount: Decimal
    status: str


class ClaimOut(BaseModel):
    claim_id: int
    user_id: int
    policy_id: int
    claim_type: str
    claim_amount: Decimal
    status: str
    priority: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)


# Authentication schemas
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    phone_number: str | None = None
    password: str = Field(min_length=8)


class UserSignupResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    phone_number: str | None
    role: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
