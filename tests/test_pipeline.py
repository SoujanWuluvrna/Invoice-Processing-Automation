import pytest
from unittest.mock import patch
from agents.orchestrator import Orchestrator
from models.invoice_model import InvoiceModel, InvoiceItem
from models.validation_model import ValidationModel
from models.decision_model import DecisionModel

MOCK_INVOICE = InvoiceModel(
    vendor="Widgets Inc.",
    items=[InvoiceItem(name="WidgetA", qty=5, price=250.0)],
    total=1250.0,
    due_date="2026-02-01"
)

def test_orchestrator_initializes():
    orchestrator = Orchestrator()
    assert orchestrator.ingestion_agent is not None
    assert orchestrator.validation_agent is not None
    assert orchestrator.approval_agent is not None
    assert orchestrator.payment_agent is not None

def test_pipeline_full_approved():
    orchestrator = Orchestrator()
    mock_decision = DecisionModel(approved=True, reasoning="All good.")

    with patch.object(orchestrator.ingestion_agent, "run", return_value=MOCK_INVOICE), \
         patch.object(orchestrator.approval_agent, "run", return_value=mock_decision):
        result = orchestrator.run("data/invoices/invoice_1001.txt")

    assert result["status"] == "APPROVED"
    assert result["payment"]["status"] == "success"

def test_pipeline_rejected_on_validation_failure():
    orchestrator = Orchestrator()
    failed_validation = ValidationModel(is_valid=False, errors=["Item not found."])
    mock_decision = DecisionModel(approved=False, reasoning="Validation errors.")

    with patch.object(orchestrator.ingestion_agent, "run", return_value=MOCK_INVOICE), \
         patch.object(orchestrator.validation_agent, "run", return_value=failed_validation), \
         patch.object(orchestrator.approval_agent, "run", return_value=mock_decision):
        result = orchestrator.run("data/invoices/invoice_1001.txt")

    assert result["status"] == "REJECTED"

def test_pipeline_aborts_on_ingestion_failure():
    orchestrator = Orchestrator()
    with patch.object(orchestrator.ingestion_agent, "run", side_effect=Exception("parse error")):
        result = orchestrator.run("data/invoices/bad_file.txt")

    assert result["status"] == "FAILED"
    assert "Ingestion failed" in result["error"]
