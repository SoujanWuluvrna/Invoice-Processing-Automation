import pytest
from unittest.mock import patch
from agents.approval_agent import ApprovalAgent
from models.invoice_model import InvoiceModel, InvoiceItem
from models.validation_model import ValidationModel
from models.decision_model import DecisionModel

VALID_INVOICE = InvoiceModel(
    vendor="Widgets Inc.",
    items=[InvoiceItem(name="WidgetA", qty=5, price=250.0)],
    total=1250.0,
    due_date="2026-02-01"
)

VALID_VALIDATION = ValidationModel(is_valid=True, errors=[])
INVALID_VALIDATION = ValidationModel(is_valid=False, errors=["Item not found in inventory."])

def test_approval_auto_rejects_invalid_invoice():
    agent = ApprovalAgent()
    result = agent.run(VALID_INVOICE, INVALID_VALIDATION)
    assert result.approved is False
    assert "validation" in result.reasoning.lower()

def test_approval_approves_valid_invoice():
    agent = ApprovalAgent()
    mock_decision = DecisionModel(approved=True, reasoning="Invoice looks good.")
    with patch("agents.approval_agent.llm_service.generate_structured_response", return_value=mock_decision):
        result = agent.run(VALID_INVOICE, VALID_VALIDATION)
    assert result.approved is True

def test_approval_handles_llm_error_gracefully():
    agent = ApprovalAgent()
    with patch("agents.approval_agent.llm_service.generate_structured_response", side_effect=Exception("timeout")):
        result = agent.run(VALID_INVOICE, VALID_VALIDATION)
    assert result.approved is False
    assert "error" in result.reasoning.lower()

def test_approval_flags_high_value_invoice():
    agent = ApprovalAgent()
    high_value_invoice = InvoiceModel(
        vendor="Atlas Industrial",
        items=[InvoiceItem(name="GadgetX", qty=5, price=3000.0)],
        total=15000.0,
        due_date="2026-03-01"
    )
    mock_decision = DecisionModel(approved=True, reasoning="High value but verified.")
    with patch("agents.approval_agent.llm_service.generate_structured_response", return_value=mock_decision) as mock_llm:
        result = agent.run(high_value_invoice, VALID_VALIDATION)
        # Verify the prompt included high value warning
        call_args = mock_llm.call_args
        assert "HIGH VALUE" in call_args.kwargs.get("user_prompt", "") or \
               "HIGH VALUE" in str(call_args)
    assert result.approved is True
