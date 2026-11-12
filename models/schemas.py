from pydantic import BaseModel, Field
from typing import Optional, Literal


class PolicyholderDetails(BaseModel):
    name: str
    email: str
    phone_number: int


class CreateClaim(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    claim_type: str
    claim_amount: float = Field(gt=0, lt=100000)
    policyholder: PolicyholderDetails
    description: Optional[str] = None


class UpdateClaim(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    claim_type: str
    status: Literal["Pending", "Approved", "Rejected"]
    claim_amount: float = Field(gt=0, lt=100000)
    policyholder: PolicyholderDetails
    description: Optional[str] = None


class CreateClaimDetailResponse(BaseModel):
    policy_number: str
    claim_type: str
    claim_amount: float


class CreateClaimResponse(BaseModel):
    message: str
    claim: CreateClaimDetailResponse


class ClaimsResponse(BaseModel):
    claim_id: int
    policy_number: str
    claim_type: str
    claim_amount: float
    status: str
