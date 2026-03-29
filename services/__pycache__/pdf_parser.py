import os
import csv
import json

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

from utils.logger import get_logger

logger = get_logger("PDF_PARSER")

def extract_text(file_path: str) -> str:
    """Extracts text from a PDF, TXT, CSV, or JSON file."""
    if not os.path.exists(file_path):
        logger.error("File not found: %s" % file_path)
        raise FileNotFoundError("File not found: %s" % file_path)

    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.txt':
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    elif ext == '.csv':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            if not rows:
                return ""
            headers = list(rows[0].keys())
            lines = [", ".join(headers)]
            for row in rows:
                lines.append(", ".join(str(v) for v in row.values()))
            return "\n".join(lines)
        except Exception as e:
            logger.error("Error reading CSV %s: %s" % (file_path, e))
            raise

    elif ext == '.json':
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return json.dumps(data, indent=2)
        except Exception as e:
            logger.error("Error reading JSON %s: %s" % (file_path, e))
            raise

    elif ext == '.pdf':
        if PdfReader is None:
            logger.error("PyPDF2 is not installed. Cannot parse PDF.")
            raise ImportError("PyPDF2 is required for PDF parsing. Run: pip install PyPDF2")
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        except Exception as e:
            logger.error("Error reading PDF %s: %s" % (file_path, e))
            raise

    else:
        logger.error("Unsupported file type: %s" % ext)
        raise ValueError("Unsupported file type: %s" % ext)
