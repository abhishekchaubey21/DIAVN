import json
import logging
import time
from typing import Tuple, Optional
from pydantic import ValidationError
from google.genai import types

from app.core.config import settings
from app.ai.gemini_client import get_gemini_client
from app.schemas.invoice_extraction import InvoiceExtraction

logger = logging.getLogger(__name__)

EXTRACTION_SYSTEM_INSTRUCTION = (
    "You are an objective document extraction system for equipment loan verification. "
    "Your role is STRICTLY factual evidence extraction from the supplied invoice document.\n\n"
    "CRITICAL EXTRACTION RULES:\n"
    "1. Extract only visible factual fields from the provided document.\n"
    "2. Do NOT infer, extrapolate, or guess values that are not clearly visible.\n"
    "3. Return null for any field that cannot be reliably extracted from the invoice.\n"
    "4. Preserve numbers, HSN codes, serial numbers, and tax figures exactly as visible.\n"
    "5. Extract itemized rows into the items list with quantity, unit_price, total_amount, and serial numbers.\n"
    "6. Do NOT evaluate risk, do NOT calculate fraud scores, and do NOT make lending decisions.\n"
    "7. Assign extraction_confidence between 0.0 (unreadable/illegible) and 1.0 (crisp, complete extraction)."
)


class InvoiceExtractor:
    def __init__(self):
        self.model_name = settings.GEMINI_MODEL

    def extract_from_bytes(
        self,
        file_bytes: bytes,
        content_type: str = "application/pdf"
    ) -> Tuple[bool, Optional[InvoiceExtraction], Optional[str], float]:
        """
        Extract structured invoice data using Gemini Free Tier.
        Returns: (success: bool, extraction: Optional[InvoiceExtraction], error_message: Optional[str], duration_seconds: float)
        """
        start_time = time.time()
        client = get_gemini_client()

        if not client:
            duration = time.time() - start_time
            msg = "Gemini API key is not configured. Extraction unavailable; original document preserved."
            logger.info(msg)
            return False, None, msg, duration

        # Normalize content type for Gemini Part
        mime_type = content_type
        if mime_type not in ["application/pdf", "image/jpeg", "image/png", "image/webp"]:
            mime_type = "application/pdf"

        try:
            logger.info(f"Starting Gemini invoice extraction using free-tier model '{self.model_name}' (size: {len(file_bytes)} bytes)")
            
            document_part = types.Part.from_bytes(
                data=file_bytes,
                mime_type=mime_type
            )

            prompt = (
                "Please extract all visible invoice metadata, dealer details, customer details, "
                "itemized lines with serial numbers, tax amounts, and total amounts from this invoice document."
            )

            response = client.models.generate_content(
                model=self.model_name,
                contents=[document_part, prompt],
                config=types.GenerateContentConfig(
                    system_instruction=EXTRACTION_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=InvoiceExtraction,
                    temperature=0.0  # Zero temperature for deterministic factual extraction
                )
            )

            duration = time.time() - start_time
            raw_text = response.text

            if not raw_text:
                msg = "Gemini returned an empty response."
                logger.warning(msg)
                return False, None, msg, duration

            # Parse and validate with Pydantic schema
            try:
                parsed_json = json.loads(raw_text)
                extraction = InvoiceExtraction.model_validate(parsed_json)
                logger.info(f"Successfully extracted invoice #{extraction.invoice_number} in {duration:.2f}s (confidence: {extraction.extraction_confidence:.2f})")
                return True, extraction, None, duration
            except (json.JSONDecodeError, ValidationError) as parse_err:
                msg = f"Failed to validate structured extraction against schema: {parse_err}"
                logger.error(msg)
                return False, None, "Malformed extraction output from model. Original document preserved.", duration

        except Exception as e:
            duration = time.time() - start_time
            msg = f"Gemini API extraction failed: {e}"
            logger.error(msg)
            return False, None, "Invoice extraction unavailable. Original document preserved.", duration


invoice_extractor = InvoiceExtractor()
