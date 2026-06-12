import os
import json
import logging
import vertexai
from vertexai.generative_models import GenerativeModel
from typing import Dict, Any

logger = logging.getLogger(__name__)


class IntentRouter:
    def __init__(self):
        self.project_id = os.environ.get("GCP_PROJECT_ID")
        self.location = "us-central1"

        if not self.project_id:
            logger.warning("GCP_PROJECT_ID not set! AI routing will fail.")
            self.model = None
            return

        vertexai.init(project=self.project_id, location=self.location)

        system_instruction = """
        You are an intelligent router for an Enterprise ERP system.
        Your ONLY job is to extract filter parameters from the user's question and evaluate if the question is supported.
        DO NOT generate SQL. DO NOT answer the question directly.

        SUPPORTED TOPICS: General revenue, sales, orders, and items sold.
        UNSUPPORTED TOPICS: Specific products (e.g., "Apple", "Laptops"), employee data, weather, sports, etc.
        If a user asks about an unsupported topic, set "is_supported_question" to false.

        Extract these specific parameters if they exist in the text:
        - sales_org: Usually a 4-character code (e.g., GB01, US01, DE01).
        - currency: A 3-letter currency code (e.g., GBP, USD, EUR).

        You MUST return ONLY a valid JSON object. No markdown, no explanations.
        If a parameter is not mentioned, return null for that field.

        Example Supported Output: {"sales_org": "GB01", "currency": null, "is_supported_question": true}
        Example Unsupported Output: {"sales_org": null, "currency": null, "is_supported_question": false}
        """

        self.model = GenerativeModel("gemini-2.5-flash-lite")
        self.system_instruction = system_instruction
        logger.info(
            f"Vertex AI IntentRouter initialised — "
            f"project={self.project_id}, location={self.location}"
        )

    def extract_intent(self, user_question: str) -> Dict[str, Any]:
        """
        Passes the user's question to Gemini to extract JSON filter parameters
        and evaluate whether the question is supported by the platform.

        Args:
            user_question: The natural language question from the user.

        Returns:
            Dictionary with extracted parameters and is_supported_question flag.
            Defaults to is_supported_question=False on any failure — safe by design.
        """
        if not self.model:
            logger.error("Vertex AI model not initialised. Check GCP_PROJECT_ID.")
            return {"sales_org": None, "currency": None, "is_supported_question": False}

        try:
            logger.info(f"Routing question through Vertex AI: '{user_question}'")

            prompt = f"{self.system_instruction}\n\nUser Question: {user_question}\nOutput JSON:"
            response = self.model.generate_content(prompt)

            # Clean up response in case the model adds markdown fences
            raw_text = response.text.replace("```json", "").replace("```", "").strip()

            intent = json.loads(raw_text)

            extracted = {
                "sales_org": intent.get("sales_org"),
                "currency": intent.get("currency"),
                # Default to True if missing benefit of the doubt for valid ERP questions
                "is_supported_question": intent.get("is_supported_question", True),
            }
            logger.info(f"Extracted intent: {extracted}")
            return extracted

        except json.JSONDecodeError:
            logger.error(f"Vertex AI returned invalid JSON: {response.text}")
            return {"sales_org": None, "currency": None, "is_supported_question": False}

        except Exception as e:
            logger.error(f"Vertex AI API call failed: {str(e)}")
            return {"sales_org": None, "currency": None, "is_supported_question": False}