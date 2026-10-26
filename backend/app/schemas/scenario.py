from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ScenarioItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    description: str
    event_type: str
    drone_id: str
    site_id: str
    expected_outcome: str
    expected_policy_decision: str
    payload: Dict[str, Any]


class ScenarioRunRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    scenario_id: str = Field(..., description="ID of scenario to run")
    operator_role: Optional[str] = Field("demo_operator", description="Operator role for scenario execution")
