-- =============================================================================
-- Model:      stg_sap_sales_items
-- Layer:      Silver (Staging)
-- Source:     bronze_sap_raw.raw_sap_vbap
-- Description: Cleans and types the raw SAP VBAP sales order item data.
--              Renames SAP technical field names to business-friendly columns,
--              casts data types explicitly, and calculates line item total value.
-- =============================================================================

with
    source
    as
    (

        select *
        from {{ source
    ('bronze_sap_raw', 'raw_sap_vbap') }}

),

cleaned as
(

    select
    -- Keys
    MANDT                                       as client_id,
    VBELN                                       as sales_order_number,
    POSNR                                       as item_number,

    -- Product
    MATNR                                       as material_number,

    -- Quantity & Pricing
    cast(KWMENG as int64)                       as order_quantity,
    VRKME                                       as unit_of_measure,
    cast(NETPR as numeric)                      as net_price_per_unit,

    -- Derived: line item total value
    cast(KWMENG as numeric) * cast(NETPR as numeric) as line_item_total_value

from source

where
        -- Filter out any records with missing critical keys
        VBELN is not null
    and POSNR is not null
    and KWMENG > 0
    and NETPR > 0

)

select *
from cleaned