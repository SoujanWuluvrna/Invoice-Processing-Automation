from models.invoice_model import InvoiceModel
from models.validation_model import ValidationModel
from models.decision_model import DecisionModel
from services.llm_service import llm_service
from config.prompts import APPROVAL_SYSTEM_PROMPT
from config.settings import settings
from utils.logger import get_logger

logger = get_logger("APPROVAL_AGENT")

class ApprovalAgent:
    def run(self, invoice: InvoiceModel, validation: ValidationModel) -> DecisionModel:
        logger.info("Starting approval process...")

        # Fast-fail if validation didn't pass
        if not validation.is_valid:
            logger.warning("Invoice failed validation. Auto-rejecting.")
            return DecisionModel(
                approved=False,
                reasoning="Invoice rejected due to validation errors: %s" % "; ".join(validation.errors)
            )

        # Build approval prompt
        high_value = invoice.total > settings.high_value_threshold
        user_prompt = (
            "Please review this invoice for approval:\n"
            "Vendor: %s\n"
            "Items: %s\n"
            "Total: $%.2f\n"
            "Due Date: %s\n"
            "%s"
        ) % (
            invoice.vendor,
            ", ".join("%s x%d @ $%.2f" % (i.name, i.qty, i.price) for i in invoice.items),
            invoice.total,
            invoice.due_date or "Not specified",
            "⚠️ HIGH VALUE INVOICE (above $%.0f threshold) — apply extra scrutiny." % settings.high_value_threshold
            if high_value else ""
        )

        try:
            decision = llm_service.generate_structured_response(
                system_prompt=APPROVAL_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                response_model=DecisionModel,
            )
            if decision.approved:
                logger.info("Invoice approved. Reason: %s" % decision.reasoning)
            else:
                logger.warning("Invoice rejected. Reason: %s" % decision.reasoning)
            return decision
        except Exception as e:
            logger.error("Approval LLM call failed: %s" % e)
            return DecisionModel(
                approved=False,
                reasoning="Approval agent encountered an error: %s" % str(e)
            )
