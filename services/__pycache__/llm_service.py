import json
import time
import re
from enum import Enum
from typing import Any, Type
from pydantic import BaseModel

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:
    genai = None

from config.settings import settings
from utils.logger import get_logger

logger = get_logger("LLM_SERVICE")


class _RateLimitExhausted(Exception):
    """Raised when Gemini 429s persist across all retry attempts."""


class ModelType(Enum):
    GROK = "grok"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class LLMService:
    def __init__(self):
        self.grok_client = None
        self.gemini_client = None
        self.ollama_client = None

        # --- Grok ---
        if OpenAI:
            if settings.grok_api_key:
                self.grok_client = OpenAI(
                    api_key=settings.grok_api_key,
                    base_url="https://api.x.ai/v1"
                )
                logger.info("Grok client initialized.")
            else:
                logger.warning("GROK_API_KEY not found in environment. Grok client not initialized.")
        else:
            logger.warning("openai package is not installed. Grok client not available.")

        # --- Gemini ---
        if genai:
            if settings.gemini_api_key:
                self.gemini_client = genai.Client(api_key=settings.gemini_api_key)
                logger.info("Gemini client initialized.")
            else:
                logger.warning("GEMINI_API_KEY not found in environment. Gemini client not initialized.")
        else:
            logger.warning("google-genai package is not installed. Gemini client not available.")

        # --- Ollama (local, no API key needed) ---
        if OpenAI:
            try:
                self.ollama_client = OpenAI(
                    api_key="ollama",
                    base_url=settings.ollama_base_url,
                )
                logger.info("Ollama client initialized (model: %s)." % settings.ollama_model)
            except Exception as e:
                logger.warning("Ollama client could not be initialized: %s" % e)
        else:
            logger.warning("openai package is not installed. Ollama client not available.")

    def _build_schema_prompt(self, response_model: Type[BaseModel]) -> str:
        """
        Builds a model-specific explicit prompt so small local models know
        exactly what JSON shape to return for each response model.
        """
        schema = response_model.model_json_schema()
        name = response_model.__name__

        if name == "DecisionModel":
            return (
                "\n\nYou must respond with ONLY a JSON object with exactly these two fields:"
                "\n- approved: a boolean (true or false) indicating if the invoice should be paid"
                "\n- reasoning: a string explaining your decision"
                "\nDo NOT return invoice data. Do NOT return any other fields."
                "\nDo NOT add explanation, markdown, or code fences."
                "\nExample output:"
                '\n{"approved": true, "reasoning": "Invoice is from a known vendor, items and total look correct."}'
                "\nAnother example:"
                '\n{"approved": false, "reasoning": "Total does not match line items, possible error."}'
            )

        if name == "ValidationModel":
            return (
                "\n\nYou must respond with ONLY a JSON object with exactly these two fields:"
                "\n- is_valid: a boolean (true or false)"
                "\n- errors: a list of strings describing any errors (empty list if valid)"
                "\nDo NOT add explanation, markdown, or code fences."
                "\nExample output:"
                '\n{"is_valid": true, "errors": []}'
            )

        # Default: InvoiceModel extraction
        return (
            "\n\nExtract data from the invoice text and return ONLY a valid JSON object."
            "\nRules:"
            "\n- vendor: a single string with the vendor/supplier name"
            "\n- items: a list of objects, each with keys: name (string), qty (integer), price (float)"
            "\n- total: a single float with the final total amount (after tax if present)"
            "\n- due_date: a string in YYYY-MM-DD format, or null if not present"
            "\n- Map quantity->qty, unit_price->price, line_items->items, item->name if needed"
            "\n- If vendor is a nested object, extract just the name string"
            "\n- Convert dates to YYYY-MM-DD format (e.g. '25-Feb-2026' -> '2026-02-25')"
            "\nDo NOT return the schema. Do NOT add explanation. Do NOT use markdown or code fences."
            "\nExample output:"
            '\n{"vendor": "Acme Corp", "items": [{"name": "WidgetA", "qty": 2, "price": 250.0}], "total": 500.0, "due_date": "2026-02-01"}'
            "\nFull schema for reference: " + json.dumps(schema)
        )

    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
        model_type: ModelType = ModelType.OLLAMA,
    ) -> Any:
        """
        Generates a structured response matching the provided Pydantic model.
        Defaults to Ollama (local, no API key required).
        """
        full_system_prompt = system_prompt + self._build_schema_prompt(response_model)

        if model_type == ModelType.OLLAMA:
            if not self.ollama_client:
                raise ValueError("Ollama client not available. Ensure openai package is installed and Ollama is running.")
            try:
                return self._call_model(
                    self.ollama_client, settings.ollama_model,
                    full_system_prompt, user_prompt, response_model,
                    strip_fences=True
                )
            except Exception as e:
                logger.error("Ollama API call failed: %s" % e)
                raise

        elif model_type == ModelType.GEMINI:
            if not self.gemini_client:
                raise ValueError("Gemini LLM client not configured. Set GEMINI_API_KEY and install google-genai.")
            try:
                return self._call_gemini(full_system_prompt, user_prompt, response_model)
            except _RateLimitExhausted as e:
                if self.grok_client:
                    logger.warning("Gemini quota exhausted. Falling back to Grok. (%s)" % e)
                    try:
                        return self._call_model(self.grok_client, "grok-3-latest", full_system_prompt, user_prompt, response_model)
                    except Exception as grok_err:
                        logger.error("Grok fallback also failed: %s" % grok_err)
                        raise grok_err
                else:
                    logger.error("Gemini quota exhausted and no Grok client available for fallback.")
                    raise
            except Exception as e:
                logger.error("Gemini API call failed: %s" % e)
                raise

        elif model_type == ModelType.GROK:
            if not self.grok_client:
                raise ValueError("Grok LLM client not configured. Set GROK_API_KEY.")
            try:
                return self._call_model(self.grok_client, "grok-3-latest", full_system_prompt, user_prompt, response_model)
            except Exception as e:
                logger.error("Grok API call failed: %s" % e)
                raise

        else:
            raise ValueError("Unsupported model_type: %s" % model_type)

    def _call_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
        max_retries: int = 3,
        base_delay: float = 5.0,
    ) -> Any:
        model_name = "gemini-2.0-flash"
        last_exc = None

        for attempt in range(1, max_retries + 1):
            logger.info("Calling LLM: %s (attempt %d/%d)" % (model_name, attempt, max_retries))
            try:
                response = self.gemini_client.models.generate_content(
                    model=model_name,
                    contents=user_prompt,
                    config=genai_types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        response_mime_type="application/json",
                        temperature=0.0,
                    ),
                )
                content = response.text
                logger.debug("LLM Raw Response: %s" % content)
                data = json.loads(content)
                return response_model(**data)
            except Exception as exc:
                err_str = str(exc)
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                    last_exc = exc
                    suggested = self._parse_retry_delay(err_str)
                    delay = suggested if suggested else base_delay * (2 ** (attempt - 1))
                    if attempt < max_retries:
                        logger.warning("Gemini 429 on attempt %d. Retrying in %.1fs..." % (attempt, delay))
                        time.sleep(delay)
                    else:
                        logger.error("Gemini 429 persists after %d attempts." % max_retries)
                else:
                    raise

        raise _RateLimitExhausted("Gemini rate limit not resolved after %d retries" % max_retries) from last_exc

    @staticmethod
    def _parse_retry_delay(error_str: str) -> float:
        match = re.search(r"'retryDelay':\s*'(\d+)s'", error_str)
        if match:
            return float(match.group(1))
        match = re.search(r"please retry in ([\d.]+)s", error_str, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 0.0

    def _call_model(
        self,
        client,
        model_name: str,
        system_prompt: str,
        user_prompt: str,
        response_model: Type[BaseModel],
        strip_fences: bool = False,
    ) -> Any:
        logger.info("Calling LLM: %s" % model_name)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        content = response.choices[0].message.content
        logger.debug("LLM Raw Response: %s" % content)

        if strip_fences:
            content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip())

        try:
            data = json.loads(content)
            return response_model(**data)
        except Exception as e:
            logger.error("Failed to parse LLM response into %s: %s" % (response_model.__name__, e))
            raise


# Singleton instance
llm_service = LLMService()