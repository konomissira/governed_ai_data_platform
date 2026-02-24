import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from google.cloud import bigquery
from google.api_core.exceptions import GoogleAPICallError

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
# Pulled from environment variables — never hardcode GCP project IDs
PROJECT_ID = os.environ.get("GCP_PROJECT_ID", "governed-ai-data-platform")
DATASET_ID = os.environ.get("GCP_DATASET_ID", "bronze_sap_raw")
DATASET_REGION = os.environ.get("GCP_DATASET_REGION", "EU")

# --- SCHEMA DEFINITIONS ---
# Explicit schemas prevent BigQuery auto-detect surprises in production
VBAK_SCHEMA = [
    bigquery.SchemaField("MANDT",  "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("VBELN",  "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("ERDAT",  "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("ERNAM",  "STRING",    mode="NULLABLE"),
    bigquery.SchemaField("VKORG",  "STRING",    mode="NULLABLE"),
    bigquery.SchemaField("VTWEG",  "STRING",    mode="NULLABLE"),
    bigquery.SchemaField("NETWR",  "FLOAT64",   mode="NULLABLE"),
    bigquery.SchemaField("WAERK",  "STRING",    mode="NULLABLE"),
    bigquery.SchemaField("KUNNR",  "STRING",    mode="NULLABLE"),
]

VBAP_SCHEMA = [
    bigquery.SchemaField("MANDT",  "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("VBELN",  "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("POSNR",  "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("MATNR",  "STRING",    mode="NULLABLE"),
    bigquery.SchemaField("KWMENG", "INT64",     mode="NULLABLE"),
    bigquery.SchemaField("VRKME",  "STRING",    mode="NULLABLE"),
    bigquery.SchemaField("NETPR",  "FLOAT64",   mode="NULLABLE"),
]

# --- DATA GENERATION ---
def generate_vbak_data(num_records: int = 1000) -> pd.DataFrame:
    """
    Generates mock SAP Sales Document Header Data (VBAK).

    Args:
        num_records: Number of sales order headers to generate.

    Returns:
        DataFrame with VBAK structure.
    """
    logger.info(f"Generating VBAK (Sales Header) data — {num_records} records...")
    rng = np.random.default_rng(seed=42)  # Seeded for reproducibility
    dates = [datetime.today() - timedelta(days=x) for x in range(365)]

    data = {
        "MANDT": ["100"] * num_records,
        "VBELN": [f"1000{i:05d}" for i in range(num_records)],
        "ERDAT": rng.choice(dates, num_records),
        "ERNAM": ["BATCH_USER"] * num_records,
        "VKORG": rng.choice(["GB01", "US01", "DE01"], num_records),
        "VTWEG": rng.choice(["10", "20"], num_records),
        "NETWR": np.round(rng.uniform(100.0, 10000.0, num_records), 2),
        "WAERK": ["GBP"] * num_records,
        "KUNNR": [f"CUST{rng.integers(100, 999)}" for _ in range(num_records)],
    }
    df = pd.DataFrame(data)
    logger.info(f"VBAK generation complete — {len(df)} rows.")
    return df


def generate_vbap_data(vbak_df: pd.DataFrame, max_items_per_order: int = 4) -> pd.DataFrame:
    """
    Generates mock SAP Sales Document Item Data (VBAP).
    Uses vectorised operations instead of iterrows() for performance.

    Args:
        vbak_df: The VBAK header DataFrame to generate items for.
        max_items_per_order: Maximum line items per sales order.

    Returns:
        DataFrame with VBAP structure.
    """
    logger.info("Generating VBAP (Sales Item) data...")
    rng = np.random.default_rng(seed=42)

    num_orders = len(vbak_df)
    items_per_order = rng.integers(1, max_items_per_order + 1, size=num_orders)
    total_items = items_per_order.sum()

    # Repeat header fields across items — vectorised, no iterrows()
    repeated_mandt = np.repeat(vbak_df["MANDT"].values, items_per_order)
    repeated_vbeln = np.repeat(vbak_df["VBELN"].values, items_per_order)

    # Build item sequence numbers per order (10, 20, 30...)
    posnr = np.concatenate([
        np.arange(1, n + 1) * 10 for n in items_per_order
    ])

    df = pd.DataFrame({
        "MANDT":  repeated_mandt,
        "VBELN":  repeated_vbeln,
        "POSNR":  [f"{p:06d}" for p in posnr],
        "MATNR":  [f"PROD-{rng.integers(1000, 1050)}" for _ in range(total_items)],
        "KWMENG": rng.integers(1, 50, size=total_items),
        "VRKME":  ["EA"] * total_items,
        "NETPR":  np.round(rng.uniform(10.0, 500.0, total_items), 2),
    })

    logger.info(f"VBAP generation complete — {len(df)} rows.")
    return df


# --- BIGQUERY UPLOAD ---
def get_bigquery_client(project_id: str) -> bigquery.Client:
    """
    Creates a BigQuery client using Application Default Credentials (ADC).
    ADC supports service account keys locally and Workload Identity in production.

    Args:
        project_id: GCP project ID.

    Returns:
        Authenticated BigQuery client.
    """
    logger.info(f"Initialising BigQuery client for project: {project_id}")
    return bigquery.Client(project=project_id)


def ensure_dataset_exists(client: bigquery.Client, dataset_id: str, location: str) -> None:
    """
    Creates the BigQuery dataset if it does not already exist.

    Args:
        client: Authenticated BigQuery client.
        dataset_id: Target dataset ID.
        location: GCP region for the dataset.
    """
    dataset_ref = client.dataset(dataset_id)
    try:
        client.get_dataset(dataset_ref)
        logger.info(f"Dataset '{dataset_id}' already exists.")
    except GoogleAPICallError:
        logger.info(f"Dataset '{dataset_id}' not found — creating in region '{location}'...")
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = location
        client.create_dataset(dataset)
        logger.info(f"Dataset '{dataset_id}' created successfully.")


def upload_to_bigquery(
    df: pd.DataFrame,
    table_name: str,
    project_id: str,
    dataset_id: str,
    schema: list,
    location: str = "EU",
) -> None:
    """
    Uploads a Pandas DataFrame to a BigQuery table with an explicit schema.

    Args:
        df: DataFrame to upload.
        table_name: Target BigQuery table name.
        project_id: GCP project ID.
        dataset_id: Target dataset ID.
        schema: Explicit BigQuery schema field list.
        location: GCP region for the dataset.

    Raises:
        GoogleAPICallError: If the BigQuery upload job fails.
        Exception: For any unexpected errors during upload.
    """
    client = get_bigquery_client(project_id)
    ensure_dataset_exists(client, dataset_id, location)

    table_id = f"{project_id}.{dataset_id}.{table_name}"
    logger.info(f"Uploading {len(df)} rows to '{table_id}'...")

    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition="WRITE_TRUNCATE",
        # Parquet is faster and more type-safe than the default JSON format
        source_format=bigquery.SourceFormat.PARQUET,
    )

    try:
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()  # Block until complete
        logger.info(f"Successfully uploaded {len(df)} rows to '{table_id}'.")
    except GoogleAPICallError as e:
        logger.error(f"BigQuery API error uploading to '{table_id}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error uploading to '{table_id}': {e}")
        raise


# --- ENTRYPOINT ---
def validate_config() -> bool:
    """
    Validates required environment variables are set before running.

    Returns:
        True if config is valid, False otherwise.
    """
    if not PROJECT_ID:
        logger.error(
            "GCP_PROJECT_ID environment variable is not set. "
            "Please run: export GCP_PROJECT_ID='your-actual-project-id'"
        )
        return False
    if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        logger.warning(
            "GOOGLE_APPLICATION_CREDENTIALS is not set. "
            "Falling back to Application Default Credentials (ADC). "
            "If running locally, ensure you have run: gcloud auth application-default login"
        )
    return True


if __name__ == "__main__":
    logger.info("=== SAP Data Generation Pipeline Starting ===")

    if not validate_config():
        raise SystemExit(1)

    # 1. Generate data
    vbak_df = generate_vbak_data(num_records=1500)
    vbap_df = generate_vbap_data(vbak_df, max_items_per_order=4)

    # 2. Upload to BigQuery
    logger.info("Connecting to GCP BigQuery...")
    upload_to_bigquery(vbak_df, "raw_sap_vbak", PROJECT_ID, DATASET_ID, VBAK_SCHEMA, DATASET_REGION)
    upload_to_bigquery(vbap_df, "raw_sap_vbap", PROJECT_ID, DATASET_ID, VBAP_SCHEMA, DATASET_REGION)

    logger.info("=== Pipeline Complete - check your BigQuery console. ===")