from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal
from decimal import Decimal


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


class ClaimCreate(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    claim_type: str
    claim_amount: Decimal = Field(gt=0, lt=100000)
    description: Optional[str] = None


class ClaimOut(BaseModel):
    claim_id: int
    policy_id: int
    claim_type: str
    claim_amount: Decimal
    status: str
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ClaimUpdate(BaseModel):
    policy_number: str = Field(min_length=5, max_length=10)
    claim_type: str
    status: Literal["Pending", "Approved", "Rejected"]
    claim_amount: Decimal = Field(gt=0, lt=100000)
    description: Optional[str] = None


class ClaimPatch(BaseModel):
    claim_type: Optional[str] = None
    claim_amount: Optional[Decimal] = Field(default=None, gt=0, lt=100000)
    status: Optional[Literal["Pending", "Approved", "Rejected"]] = None
    description: Optional[str] = None
