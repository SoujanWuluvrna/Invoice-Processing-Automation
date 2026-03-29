from utils.logger import get_logger

logger = get_logger("PAYMENT_SERVICE")

def mock_payment(vendor: str, amount: float) -> dict:
    """Simulates a payment execution."""
    logger.info("Executing mock payment of %.2f to %s" % (amount, vendor))
    # Simulate success for all valid payments
    return {
        "status": "success",
        "vendor": vendor,
        "amount": amount,
        "transaction_id": "TXN-%s-%s" % (vendor[:4].upper().replace(" ", ""), str(int(amount)))
    }
