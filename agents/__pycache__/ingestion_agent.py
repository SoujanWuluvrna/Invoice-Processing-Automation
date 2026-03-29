from services.llm_service import llm_service
from services.pdf_parser import extract_text
from models.invoice_model import InvoiceModel
from config.prompts import INGESTION_SYSTEM_PROMPT
from utils.logger import get_logger

logger = get_logger("INGESTION_AGENT")

class IngestionAgent:
    def run(self, file_path: str) -> InvoiceModel:
        logger.info("Ingesting file: %s" % file_path)
        try:
            raw_text = extract_text(file_path)
            invoice = llm_service.generate_structured_response(
                system_prompt=INGESTION_SYSTEM_PROMPT,
                user_prompt=raw_text,
                response_model=InvoiceModel,
            )
            logger.info("Successfully extracted invoice for vendor: %s" % invoice.vendor)
            return invoice
        except Exception as e:
            logger.error("Ingestion failed: %s" % e)
            raise
