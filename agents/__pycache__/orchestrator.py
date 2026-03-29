from agents.ingestion_agent import IngestionAgent
from agents.validation_agent import ValidationAgent
from agents.approval_agent import ApprovalAgent
from agents.payment_agent import PaymentAgent
from utils.logger import get_logger

logger = get_logger("ORCHESTRATOR")

class Orchestrator:
    def __init__(self):
        self.ingestion_agent = IngestionAgent()
        self.validation_agent = ValidationAgent()
        self.approval_agent = ApprovalAgent()
        self.payment_agent = PaymentAgent()

    def run(self, file_path: str) -> dict:
        logger.info("--- Starting Pipeline for %s ---" % file_path)

        result = {
            "file": file_path,
            "status": "FAILED",
            "invoice": None,
            "validation": None,
            "decision": None,
            "payment": None,
            "error": None,
        }

        # Stage 1: Ingestion
        try:
            invoice = self.ingestion_agent.run(file_path)
            result["invoice"] = invoice
        except Exception as e:
            result["error"] = "Ingestion failed: %s" % e
            logger.error("Pipeline aborted at ingestion stage.")
            return result

        # Stage 2: Validation
        try:
            validation = self.validation_agent.run(invoice)
            result["validation"] = validation
        except Exception as e:
            result["error"] = "Validation failed: %s" % e
            logger.error("Pipeline aborted at validation stage.")
            return result

        # Stage 3: Approval
        try:
            decision = self.approval_agent.run(invoice, validation)
            result["decision"] = decision
        except Exception as e:
            result["error"] = "Approval failed: %s" % e
            logger.error("Pipeline aborted at approval stage.")
            return result

        # Stage 4: Payment
        try:
            payment = self.payment_agent.run(invoice, decision)
            result["payment"] = payment
        except Exception as e:
            result["error"] = "Payment failed: %s" % e
            logger.error("Pipeline aborted at payment stage.")
            return result

        # Final status
        if decision.approved and result["payment"].get("status") == "success":
            result["status"] = "APPROVED"
        elif not decision.approved:
            result["status"] = "REJECTED"

        logger.info("--- Pipeline Finished. FINAL STATUS: %s ---" % result["status"])
        return result
