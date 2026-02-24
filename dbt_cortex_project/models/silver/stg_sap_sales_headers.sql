-- =============================================================================
-- Model:      stg_sap_sales_headers
-- Layer:      Silver (Staging)
-- Source:     bronze_sap_raw.raw_sap_vbak
-- Description: Cleans and types the raw SAP VBAK sales order header data.
--              Renames SAP technical field names to business-friendly columns,
--              casts data types explicitly, and filters out any invalid records.
-- =============================================================================

with
    source
    as
    (

        select *
        from {{ source
    
    ('bronze_sap_raw', 'raw_sap_vbak') }}

),

cleaned as
(

    select
    -- Keys
    MANDT                                   as client_id,
    VBELN                                   as sales_order_number,

    -- Dates
    cast(ERDAT as timestamp)                as created_at,

    -- Audit
    ERNAM                                   as created_by,

    -- Organisation
    VKORG                                   as sales_org,
    VTWEG                                   as distribution_channel,

    -- Financials
    cast(NETWR as numeric)                  as net_value,
    WAERK                                   as currency,

    -- Customer
    KUNNR                                   as customer_id

from source

where
        -- Filter out any records with missing critical keys
        VBELN is not null
    and KUNNR is not null
    and NETWR > 0

)

select *
from cleaned