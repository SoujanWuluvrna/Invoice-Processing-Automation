from models.invoice_model import InvoiceModel
from models.validation_model import ValidationModel
from services.db_service import db_service
from utils.helpers import normalize_item_name
from utils.logger import get_logger

logger = get_logger("VALIDATION_AGENT")

class ValidationAgent:
    def run(self, invoice: InvoiceModel) -> ValidationModel:
        logger.info("Starting validation...")
        errors = []

        # Check total is positive
        if invoice.total <= 0:
            errors.append("Invoice total must be positive, got: %.2f" % invoice.total)

        for item in invoice.items:
            # Check for negative values
            if item.qty <= 0:
                errors.append("Item '%s' has invalid quantity: %d" % (item.name, item.qty))
            if item.price <= 0:
                errors.append("Item '%s' has invalid unit price: %.2f" % (item.name, item.price))

            # Normalize name for DB lookup
            normalized = normalize_item_name(item.name)
            db_item = db_service.get_item(normalized)

            if not db_item["exists"]:
                errors.append("Item '%s' (normalized: '%s') not found in inventory." % (item.name, normalized))
            elif db_item["stock"] == 0:
                errors.append("Item '%s' is out of stock." % item.name)
            elif db_item["stock"] < item.qty:
                errors.append(
                    "Insufficient stock for '%s': requested %d, available %d."
                    % (item.name, item.qty, db_item["stock"])
                )

        is_valid = len(errors) == 0
        if is_valid:
            logger.info("Validation passed.")
        else:
            logger.warning("Validation failed with %d error(s)." % len(errors))
            for err in errors:
                logger.warning("  - %s" % err)

        return ValidationModel(is_valid=is_valid, errors=errors)
