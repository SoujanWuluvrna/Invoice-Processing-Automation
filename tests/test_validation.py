import pytest
from agents.validation_agent import ValidationAgent
from models.invoice_model import InvoiceModel, InvoiceItem

def make_invoice(items, total=5000.0):
    return InvoiceModel(vendor="Test Vendor", items=items, total=total, due_date="2026-02-01")

def test_validation_passes_for_valid_invoice():
    agent = ValidationAgent()
    invoice = make_invoice([
        InvoiceItem(name="WidgetA", qty=5, price=250.0),
        InvoiceItem(name="WidgetB", qty=3, price=500.0),
    ], total=2750.0)
    result = agent.run(invoice)
    assert result.is_valid is True
    assert result.errors == []

def test_validation_fails_for_negative_quantity():
    agent = ValidationAgent()
    invoice = make_invoice([
        InvoiceItem(name="WidgetA", qty=-1, price=250.0),
    ])
    result = agent.run(invoice)
    assert result.is_valid is False
    assert any("quantity" in e.lower() for e in result.errors)

def test_validation_fails_for_unknown_item():
    agent = ValidationAgent()
    invoice = make_invoice([
        InvoiceItem(name="UnknownGizmo", qty=2, price=100.0),
    ])
    result = agent.run(invoice)
    assert result.is_valid is False
    assert any("not found" in e.lower() for e in result.errors)

def test_validation_fails_for_stock_exceeded():
    agent = ValidationAgent()
    # WidgetA has 15 in stock, requesting 20
    invoice = make_invoice([
        InvoiceItem(name="WidgetA", qty=20, price=250.0),
    ])
    result = agent.run(invoice)
    assert result.is_valid is False
    assert any("insufficient" in e.lower() for e in result.errors)

def test_validation_fails_for_zero_stock_item():
    agent = ValidationAgent()
    invoice = make_invoice([
        InvoiceItem(name="FakeItem", qty=1, price=10.0),
    ])
    result = agent.run(invoice)
    assert result.is_valid is False
    assert any("out of stock" in e.lower() for e in result.errors)

def test_validation_fails_for_negative_price():
    agent = ValidationAgent()
    invoice = make_invoice([
        InvoiceItem(name="WidgetA", qty=2, price=-50.0),
    ])
    result = agent.run(invoice)
    assert result.is_valid is False
    assert any("price" in e.lower() for e in result.errors)
