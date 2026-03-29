import pytest
from unittest.mock import patch, MagicMock
from agents.ingestion_agent import IngestionAgent
from models.invoice_model import InvoiceModel, InvoiceItem

MOCK_INVOICE = InvoiceModel(
    vendor="Widgets Inc.",
    items=[
        InvoiceItem(name="WidgetA", qty=10, price=250.0),
        InvoiceItem(name="WidgetB", qty=5, price=500.0),
    ],
    total=5000.0,
    due_date="2026-02-01"
)

def test_ingestion_txt_success():
    agent = IngestionAgent()
    with patch("agents.ingestion_agent.extract_text", return_value="invoice text"), \
         patch("agents.ingestion_agent.llm_service.generate_structured_response", return_value=MOCK_INVOICE):
        result = agent.run("data/invoices/invoice_1001.txt")
    assert result.vendor == "Widgets Inc."
    assert result.total == 5000.0
    assert len(result.items) == 2

def test_ingestion_file_not_found():
    agent = IngestionAgent()
    with pytest.raises(Exception):
        agent.run("data/invoices/nonexistent.txt")

def test_ingestion_llm_failure():
    agent = IngestionAgent()
    with patch("agents.ingestion_agent.extract_text", return_value="invoice text"), \
         patch("agents.ingestion_agent.llm_service.generate_structured_response", side_effect=Exception("LLM error")):
        with pytest.raises(Exception, match="LLM error"):
            agent.run("data/invoices/invoice_1001.txt")

def test_ingestion_json_invoice():
    agent = IngestionAgent()
    mock_invoice = InvoiceModel(
        vendor="Precision Parts Ltd.",
        items=[InvoiceItem(name="WidgetA", qty=3, price=250.0)],
        total=1890.0,
        due_date="2026-02-22"
    )
    with patch("agents.ingestion_agent.extract_text", return_value="{}"), \
         patch("agents.ingestion_agent.llm_service.generate_structured_response", return_value=mock_invoice):
        result = agent.run("data/invoices/invoice_1004.json")
    assert result.vendor == "Precision Parts Ltd."
    assert result.due_date == "2026-02-22"
