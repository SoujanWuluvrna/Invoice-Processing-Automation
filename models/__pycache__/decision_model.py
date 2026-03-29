from pydantic import BaseModel, Field

class DecisionModel(BaseModel):
    approved: bool = Field(..., description="True if the invoice is approved for payment, False otherwise")
    reasoning: str = Field(..., description="Reasoning or explanation for the approval decision")
