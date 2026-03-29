from pydantic import BaseModel, Field
from typing import List

class ValidationModel(BaseModel):
    is_valid: bool = Field(..., description="True if the invoice passes all validation checks, False otherwise")
    errors: List[str] = Field(default_factory=list, description="List of validation error messages, if any")
