import os
import logging
from google.cloud import bigquery
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class BigQueryClient:
    def __init__(self):
        # Use the same environment variables as dbt and the data pipeline
        self.project_id = os.environ.get("GCP_PROJECT_ID")
        self.dataset_id = "bronze_sap_raw_gold"  # The dbt gold dataset

        if not self.project_id:
            logger.warning("GCP_PROJECT_ID not set! Database calls will fail.")
            self.client = None
        else:
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"BigQuery Client initialised for project: {self.project_id}")

    def get_sales_summary(
        self,
        sales_org: Optional[str] = None,
        currency: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes a STRICTLY GOVERNED, parameterised SQL query against the dbt Gold table.
        The LLM does NOT write this SQL. It only provides the filter parameters.

        Args:
            sales_org: Optional sales organisation filter (e.g. GB01, US01, DE01).
            currency: Optional currency filter (e.g. GBP, USD, EUR).

        Returns:
            Dictionary containing aggregated sales metrics or an error message.
        """
        if not self.client:
            return {"error": "BigQuery client is not initialised. Check GCP_PROJECT_ID."}

        table_ref = f"`{self.project_id}.{self.dataset_id}.fct_sales_orders`"

        # Base query using the governed dbt Gold table
        # NOTE: Column names match fct_sales_orders exactly as defined in dbt
        query = f"""
            SELECT
                COUNT(sales_order_number)       AS total_orders,
                SUM(total_quantity_ordered)     AS total_items_sold,
                SUM(order_net_value)            AS total_revenue
            FROM {table_ref}
            WHERE 1=1
        """

        # Parameterised filters prevents SQL injection and LLM hallucinations
        query_params = []

        if sales_org:
            query += " AND sales_org = @sales_org"
            query_params.append(
                bigquery.ScalarQueryParameter("sales_org", "STRING", sales_org)
            )

        if currency:
            query += " AND currency = @currency"
            query_params.append(
                bigquery.ScalarQueryParameter("currency", "STRING", currency)
            )

        job_config = bigquery.QueryJobConfig(query_parameters=query_params)

        try:
            logger.info(
                f"Executing governed query with filters: "
                f"sales_org={sales_org}, currency={currency}"
            )
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result()

            # Extract the first (and only) row this is an aggregation query
            for row in results:
                return {
                    "total_orders": row.total_orders,
                    "total_items_sold": row.total_items_sold,
                    "total_revenue": round(row.total_revenue, 2) if row.total_revenue else 0.0,
                    "filters_applied": {
                        "sales_org": sales_org,
                        "currency": currency,
                    },
                }

            return {"error": "No data found for the given filters."}

        except Exception as e:
            logger.error(f"BigQuery execution failed: {str(e)}")
            return {"error": f"Database error: {str(e)}"}