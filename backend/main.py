import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.database import BigQueryClient
from backend.ai_router import IntentRouter

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Module-level placeholders initialised during lifespan startup
bq_client: BigQueryClient = None
ai_router: IntentRouter = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler runs startup checks before the app begins
    accepting requests, ensuring credentials and config are in place.
    Replaces the old pattern of initialising clients at module level.
    """
    global bq_client, ai_router

    logger.info("=== Governed AI Data Platform — Starting Up ===")

    # Validate critical environment variables before accepting any requests
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        logger.error(
            "GCP_PROJECT_ID is not set. "
            "Please run: export GCP_PROJECT_ID='your-actual-project-id'"
        )
        raise RuntimeError("GCP_PROJECT_ID environment variable is required.")

    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.warning(
            "GOOGLE_APPLICATION_CREDENTIALS is not set. "
            "Falling back to Application Default Credentials (ADC)."
        )

    # Initialise clients after validation passes
    bq_client = BigQueryClient()
    ai_router = IntentRouter()

    logger.info("=== Startup complete — API is ready to accept requests ===")

    yield  # App runs here

    # Shutdown
    logger.info("=== Governed AI Data Platform — Shutting Down ===")


# Initialise FastAPI with lifespan and metadata
app = FastAPI(
    title="Governed AI Data Platform",
    version="1.0.0",
    description=(
        "Enterprise AI Governance API — natural language questions are routed "
        "through Vertex AI (Gemini) for parameter extraction, then executed "
        "against governed dbt Gold layer tables in BigQuery."
    ),
    lifespan=lifespan,
)


# --- Request / Response Models ---
class QuestionRequest(BaseModel):
    question: str


# --- Endpoints ---
@app.get("/")
def health_check():
    """Simple health check endpoint."""
    return {
        "status": "healthy",
        "service": "Governed AI Data Platform",
        "version": "1.0.0",
    }


@app.post("/api/ask")
def ask_question(payload: QuestionRequest):
    """
    Main governed AI endpoint.

    Flow:
    1. Vertex AI (Gemini) extracts filter parameters from the natural language question.
    2. Those parameters are passed to a pre-written, governed BigQuery SQL query.
    3. The LLM never generates SQL, it only extracts parameters.

    Example request:
        {"question": "Show me total revenue for GB01 in GBP"}

    Example response:
        {
            "question": "Show me total revenue for GB01 in GBP",
            "extracted_parameters": {"sales_org": "GB01", "currency": "GBP"},
            "data": {
                "total_orders": 312,
                "total_items_sold": 4821,
                "total_revenue": 1234567.89,
                "filters_applied": {"sales_org": "GB01", "currency": "GBP"}
            }
        }
    """
    question = payload.question
    logger.info(f"Received question: '{question}'")

    # Step 1: Use Vertex AI to extract parameters no SQL generation
    intent = ai_router.extract_intent(question)
    logger.info(f"Extracted parameters: {intent}")

    # Step 2: Query the governed dbt Gold table using extracted parameters
    result = bq_client.get_sales_summary(
        sales_org=intent.get("sales_org"),
        currency=intent.get("currency"),
    )

    if "error" in result:
        logger.error(f"Data retrieval failed: {result['error']}")
        raise HTTPException(status_code=500, detail=result["error"])

    return {
        "question": question,
        "extracted_parameters": intent,
        "data": result,
    }