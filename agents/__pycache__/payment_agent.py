from models.invoice_model import InvoiceModel
from models.decision_model import DecisionModel
from services.payment_service import mock_payment
from utils.logger import get_logger

logger = get_logger("PAYMENT_AGENT")

class PaymentAgent:
    def run(self, invoice: InvoiceModel, decision: DecisionModel) -> dict:
        logger.info("Starting payment processing...")

        if not decision.approved:
            logger.warning("Invoice not approved. Skipping payment.")
            return {"status": "skipped", "reason": decision.reasoning}

        try:
            result = mock_payment(vendor=invoice.vendor, amount=invoice.total)
            logger.info("Payment successful. Transaction ID: %s" % result.get("transaction_id"))
            return result
        except Exception as e:
            logger.error("Payment failed: %s" % e)
            return {"status": "failed", "reason": str(e)}
