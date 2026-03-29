# 🧾 Invoice AI System — Multi-Agent Invoice Processing

A local, production-quality **multi-agent AI system** that automates end-to-end invoice processing:
**Ingestion → Validation → Approval → Payment**

Built to reduce manual effort, errors, and delays in invoice workflows using **LLM-powered agents** running entirely on your machine via **Ollama** - no cloud API keys or internet connection required.

---

## 🚀 Overview

This project processes invoices (PDF, TXT, CSV, JSON) through a 4-stage AI pipeline:

| Stage | Agent | What It Does |
|---|---|---|
| **1. Ingestion** | `IngestionAgent` | Extracts structured data (vendor, items, totals, due date) from raw invoice text using a local LLM |
| **2. Validation** | `ValidationAgent` | Validates extracted items against a local SQLite inventory database (stock checks, negative values, unknown items) |
| **3. Approval** | `ApprovalAgent` | Applies business rules (e.g. high-value threshold > $10,000) + LLM reasoning to approve or reject |
| **4. Payment** | `PaymentAgent` | Executes a mock payment function and logs the result with a transaction ID |

> Designed as a working prototype that runs **fully locally** with no external dependencies beyond Ollama.

---

## 🏗️ System Architecture

```
             ┌──────────────────────┐
             │      Input File      │  (PDF / TXT / CSV / JSON)
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │   pdf_parser.py      │  Extracts raw text from file
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │   Ingestion Agent    │  LLM extracts structured InvoiceModel
             │   (llm_service)      │  vendor, items, total, due_date
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │  Validation Agent    │  SQLite inventory check
             │   (db_service)       │──► inventory.db
             └──────────┬───────────┘
                        │
                  ┌─────┴──────┐
                  │            │
              PASS           FAIL ──► Auto-reject with errors
                  │
                  ▼
             ┌──────────────────────┐
             │   Approval Agent     │  Business rules + LLM reasoning
             │   (llm_service)      │  Returns DecisionModel
             └──────────┬───────────┘
                        │
                  ┌─────┴──────┐
                  │            │
             APPROVED       REJECTED
                  │
                  ▼
             ┌──────────────────────┐
             │   Payment Agent      │  mock_payment() → transaction ID
             │  (payment_service)   │
             └──────────┬───────────┘
                        │
                        ▼
             ┌──────────────────────┐
             │     Final Result     │  APPROVED / REJECTED / FAILED
             └──────────────────────┘
```

---

## 📁 Project Structure

```
invoice_ai_system/
│
├── main.py                        # CLI entry point
│
├── config/
│   ├── settings.py                # Environment config (reads from .env)
│   └── prompts.py                 # LLM system prompts for each agent
│
├── agents/
│   ├── ingestion_agent.py         # Extracts structured data from invoices via LLM
│   ├── validation_agent.py        # Validates against SQLite inventory DB
│   ├── approval_agent.py          # Business rules + LLM-based approval reasoning
│   ├── payment_agent.py           # Mock payment execution
│   └── orchestrator.py            # Pipeline controller — runs all 4 stages
│
├── services/
│   ├── pdf_parser.py              # Text extraction: PDF, TXT, CSV, JSON
│   ├── llm_service.py             # LLM wrapper (Ollama default, Grok/Gemini optional)
│   ├── db_service.py              # SQLite inventory queries + auto-seeding
│   └── payment_service.py         # Mock payment function
│
├── models/
│   ├── invoice_model.py           # Pydantic: InvoiceModel, InvoiceItem
│   ├── validation_model.py        # Pydantic: ValidationModel
│   └── decision_model.py          # Pydantic: DecisionModel
│
├── utils/
│   ├── logger.py                  # Structured logging ([AGENT_NAME] format)
│   └── helpers.py                 # Utility functions (normalize item names, etc.)
│
├── data/
│   ├── invoices/
│   │   ├── sample.txt             # Sample invoice for quick testing
│   │   ├── invoice_1001.txt       # Plain text invoice
│   │   ├── invoice_1004.json      # JSON format invoice (nested vendor object)
│   │   ├── invoice_1006.csv       # CSV format invoice
│   │   ├── invoice_1011.pdf       # Simple PDF invoice
│   │   ├── invoice_1012.pdf       # PDF with OCR noise and formatting
│   │   └── invoice_1013.pdf       # Bulk order PDF (high-value, > $10k)
│   └── inventory.db               # SQLite DB (auto-created on first run)
│
├── tests/
│   ├── test_ingestion.py          # 4 ingestion tests (mocked LLM + parser)
│   ├── test_validation.py         # 6 validation scenarios
│   ├── test_approval.py           # 4 approval tests including high-value
│   └── test_pipeline.py           # 4 orchestrator/pipeline tests
│
├── ui/
│   └── app.py                     # Streamlit web UI
│
├── .env                           # Environment config (Ollama settings, thresholds)
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## ⚙️ Setup

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.com) installed and running

### 1. Install Ollama and Pull a Model

```bash
# macOS
brew install ollama

# Start the Ollama server
ollama serve

# Pull a model (choose one)
ollama pull llama3.2       # 3B — fast, lower accuracy
ollama pull llama3.1       # 8B — recommended, better structured output
ollama pull mistral        # 7B — excellent JSON accuracy
```

> **Recommended:** Use `llama3.1` or `mistral` for best results with structured data extraction. `llama3.2` works but may struggle with complex invoices.

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Edit the `.env` file in the project root:

```env
# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2          # Change to llama3.1 or mistral for better accuracy

# Optional cloud LLM keys (leave blank to use Ollama)
GROK_API_KEY=
GEMINI_API_KEY=

# Business rules
HIGH_VALUE_THRESHOLD=10000     # Invoices above this get extra LLM scrutiny

# Database
DB_PATH=data/inventory.db
```

### 4. Database (Auto-Created)

The SQLite inventory database is **automatically created and seeded** on first run:

| Item | Stock |
|---|---|
| WidgetA | 15 |
| WidgetB | 10 |
| GadgetX | 5 |
| FakeItem | 0 |

---

## ▶️ Running the System

### CLI Mode

```bash
python main.py --invoice_path=data/invoices/sample.txt
```

**Expected Output (approved):**
```
[LLM_SERVICE] Ollama client initialized (model: llama3.2).
[DB_SERVICE] Database initialized at data/inventory.db
[ORCHESTRATOR] --- Starting Pipeline for data/invoices/sample.txt ---
[INGESTION_AGENT] Ingesting file: data/invoices/sample.txt
[LLM_SERVICE] Calling LLM: llama3.2
[INGESTION_AGENT] Successfully extracted invoice for vendor: Tech Supplies Co.
[VALIDATION_AGENT] Starting validation...
[VALIDATION_AGENT] Validation passed.
[APPROVAL_AGENT] Starting approval process...
[LLM_SERVICE] Calling LLM: llama3.2
[APPROVAL_AGENT] Invoice approved. Reason: Invoice is valid...
[PAYMENT_AGENT] Starting payment processing...
[PAYMENT_SERVICE] Executing mock payment of 1000.00 to Tech Supplies Co.
[PAYMENT_AGENT] Payment successful.
[ORCHESTRATOR] --- Pipeline Finished. FINAL STATUS: APPROVED ---

========================================
FINAL STATUS: APPROVED
========================================
Reasoning: Invoice is valid with known items and correct totals.
Payment Status: success
Transaction ID: TXN-TECH-1000
```

### Test All Sample Invoices

```bash
python main.py --invoice_path=data/invoices/invoice_1001.txt   # Plain text
python main.py --invoice_path=data/invoices/invoice_1004.json  # JSON (nested vendor)
python main.py --invoice_path=data/invoices/invoice_1006.csv   # CSV
python main.py --invoice_path=data/invoices/invoice_1011.pdf   # Simple PDF
python main.py --invoice_path=data/invoices/invoice_1012.pdf   # OCR-noisy PDF
python main.py --invoice_path=data/invoices/invoice_1013.pdf   # Bulk/high-value PDF
```

### Streamlit Web UI

```bash
streamlit run ui/app.py
```

Then open `http://localhost:8501` in your browser.

The UI allows you to:
- Upload invoices directly from your machine
- View a live 4-stage pipeline breakdown
- See extracted line items in a table
- Review validation errors and approval reasoning

---

## 🧩 Data Models

### InvoiceModel
Extracted from raw invoice text by the Ingestion Agent.
```python
class InvoiceItem:
    name: str       # e.g., "WidgetA"
    qty: int        # e.g., 10
    price: float    # unit price e.g., 250.00

class InvoiceModel:
    vendor: str                  # e.g., "Widgets Inc."
    items: List[InvoiceItem]     # list of line items
    total: float                 # final total after tax e.g., 5000.00
    due_date: Optional[str]      # e.g., "2026-02-01" or null
```

### ValidationModel
Produced by the Validation Agent after inventory checks.
```python
class ValidationModel:
    is_valid: bool       # True if all checks pass
    errors: List[str]    # e.g., ["Insufficient stock for WidgetA: requested 20, available 15"]
```

### DecisionModel
Produced by the Approval Agent after LLM reasoning.
```python
class DecisionModel:
    approved: bool    # True if approved for payment
    reasoning: str    # LLM-generated explanation
```

---

## 🧪 Running Tests

```bash
# macOS / Linux
PYTHONPATH="." pytest tests/ -v

# Windows
$env:PYTHONPATH="."; pytest tests/ -v
```

**18 test cases** covering:

| File | Tests | What's Covered |
|---|---|---|
| `test_ingestion.py` | 4 | Success, file not found, LLM failure, JSON invoice |
| `test_validation.py` | 6 | Valid invoice, negative qty, unknown item, stock exceeded, zero stock, negative price |
| `test_approval.py` | 4 | Auto-reject on invalid, LLM approval, LLM error handling, high-value flagging |
| `test_pipeline.py` | 4 | Orchestrator init, full approved flow, rejected on validation, abort on ingestion failure |

---

## 🧠 Edge Cases Handled

| Edge Case | How It's Handled |
|---|---|
| OCR noise (`Widget A` → `WidgetA`) | Name normalization in `helpers.py` strips spaces before DB lookup |
| Nested vendor objects in JSON (`vendor.name`) | LLM prompt explicitly instructs extraction of name string only |
| Different field names (`quantity`, `unit_price`, `line_items`) | Prompt maps all common variants to the correct model fields |
| Missing due date | Pydantic `Optional[str]` with `None` default |
| Negative quantities or prices | Explicit checks in `ValidationAgent` |
| Zero-stock items (e.g. `FakeItem`) | Treated as insufficient stock — validation fails |
| Unknown inventory items | DB lookup returns `exists: false` — validation fails |
| Quantity exceeding available stock | Qty vs stock comparison in `ValidationAgent` |
| High-value invoices (> $10,000) | Extra scrutiny warning added to LLM approval prompt |
| LLM returns wrong JSON shape | Model-specific prompts per Pydantic model prevent echoing wrong data |
| LLM API failure during approval | Graceful fallback — auto-rejects with error message, pipeline continues |
| Unsupported file types | `pdf_parser.py` raises `ValueError` with clear message |

---

## 🔧 Switching LLM Models

### Change the Ollama Model

Edit `.env`:
```env
OLLAMA_MODEL=llama3.1    # or mistral, phi3, llama3.2
```

Or set it at runtime:
```bash
OLLAMA_MODEL=mistral python main.py --invoice_path=data/invoices/sample.txt
```

### Use a Cloud LLM Instead

Add your key to `.env` and pass `model_type` in the code:
```env
GEMINI_API_KEY=your_key_here
```

```python
# In agents, pass model_type=ModelType.GEMINI to generate_structured_response()
```

Supported providers: **Ollama** (default), **Gemini** (Google), **Grok** (xAI).

---

## 📊 Logging

Each agent produces structured logs:
```
[LLM_SERVICE] Ollama client initialized (model: llama3.2).
[DB_SERVICE] Database initialized at data/inventory.db
[ORCHESTRATOR] --- Starting Pipeline for invoice_1001.txt ---
[INGESTION_AGENT] Ingesting file: data/invoices/invoice_1001.txt
[LLM_SERVICE] Calling LLM: llama3.2
[INGESTION_AGENT] Successfully extracted invoice for vendor: Widgets Inc.
[VALIDATION_AGENT] Starting validation...
[VALIDATION_AGENT] Validation passed.
[APPROVAL_AGENT] Starting approval process...
[APPROVAL_AGENT] Invoice approved. Reason: Items are in stock and total is correct.
[PAYMENT_SERVICE] Executing mock payment of 5000.00 to Widgets Inc.
[PAYMENT_AGENT] Payment successful. Transaction ID: TXN-WIDG-5000
[ORCHESTRATOR] --- Pipeline Finished. FINAL STATUS: APPROVED ---
```

---

## 🌟 Future Enhancements

- Confidence scores per extracted field
- Retry / self-correction loop when LLM output fails Pydantic validation
- Batch invoice processing (directory input)
- Fraud detection rules (duplicate invoice numbers, price anomalies)
- Vendor whitelist/blacklist table in SQLite
- Dashboard analytics (processing time, approval rate, error breakdown)
- Export results to CSV/PDF report
- Email notification on approval or rejection

---

## 📄 License

For internal / evaluation use.
