from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, Literal
from decimal import Decimal


# Claim creation
class CreateClaim(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    claim_amount: Decimal = Field(gt=0, lt=100000)
    description: Optional[str] = None


class ClaimCreate(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    claim_amount: Decimal = Field(gt=0, lt=100000)
    priority: Literal["Low", "Medium", "High"] = "Medium"
    description: Optional[str] = None


# Full claim update
class UpdateClaim(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    status: Literal["Submitted", "Under Review", "Approved", "Rejected", "Settled"]
    claim_amount: Decimal = Field(gt=0, lt=100000)
    description: Optional[str] = None


class ClaimUpdate(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    status: Literal["Submitted", "Under Review", "Approved", "Rejected", "Settled"]
    priority: Literal["Low", "Medium", "High"]
    claim_amount: Decimal = Field(gt=0, lt=100000)
    description: Optional[str] = None


# Partial claim update
class ClaimPatch(BaseModel):
    claim_amount: Optional[Decimal] = Field(default=None, gt=0, lt=100000)
    status: Optional[
        Literal["Submitted", "Under Review", "Approved", "Rejected", "Settled"]
    ] = None
    priority: Optional[Literal["Low", "Medium", "High"]] = None
    description: Optional[str] = None


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
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Authentication schemas
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    phone_number: Optional[str] = None
    password: str = Field(min_length=8)


class UserSignupResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    phone_number: Optional[str]
    role: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
