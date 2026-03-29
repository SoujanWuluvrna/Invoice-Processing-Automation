from pydantic import BaseModel, Field
from typing import List, Optional

class InvoiceItem(BaseModel):
    name: str = Field(..., description="Name or description of the item")
    qty: int = Field(..., description="Quantity of the item")
    price: float = Field(..., description="Unit price of the item")

class InvoiceModel(BaseModel):
    vendor: str = Field(..., description="Name of the vendor or supplier")
    items: List[InvoiceItem] = Field(default_factory=list, description="List of items in the invoice")
    total: float = Field(..., description="Total amount of the invoice")
    due_date: Optional[str] = Field(None, description="Due date of the invoice, e.g., YYYY-MM-DD")
