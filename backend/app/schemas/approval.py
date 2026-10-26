from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    decision: str = Field(..., description="'APPROVE' or 'REJECT'")
    operator_role: str = Field(..., description="Role of the operator performing action")
    operator_id: str = Field("operator-01", description="Identifier of the operator")
    rejection_reason: Optional[str] = Field(None, description="Mandatory if decision is REJECT")
