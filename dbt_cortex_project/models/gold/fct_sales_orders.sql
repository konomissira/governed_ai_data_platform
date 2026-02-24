-- =============================================================================
-- Model:      fct_sales_orders
-- Layer:      Gold (Fact)
-- Sources:    silver.stg_sap_sales_headers, silver.stg_sap_sales_items
-- Description: Business-ready sales order fact table. Joins cleaned header and
--              item data from the Silver layer, aggregating line item metrics
--              per sales order. This table is optimised for Vertex AI consumption
--              and business reporting.
-- =============================================================================

with
    sales_headers
    as
    (

        select *
        from {{ ref
    ('stg_sap_sales_headers') }}

),

sales_items as
(

    select *
from {{ ref
('stg_sap_sales_items') }}

),

-- Aggregate item-level metrics up to order level
order_item_metrics as
(

    select
    sales_order_number,
    count(item_number)                  as total_line_items,
    sum(order_quantity)                 as total_quantity_ordered,
    sum(line_item_total_value)          as total_items_value,
    avg(net_price_per_unit)             as avg_unit_price,
    min(net_price_per_unit)             as min_unit_price,
    max(net_price_per_unit)             as max_unit_price

from sales_items
group by sales_order_number

)
,

-- Join headers with aggregated item metrics
final as
(

    select
    -- Keys & Identifiers
    h.sales_order_number,
    h.client_id,
    h.customer_id,

    -- Organisation
    h.sales_org,
    h.distribution_channel,

    -- Dates
    h.created_at,
    date(h.created_at)                  as created_date,
    extract(year from h.created_at)     as created_year,
    extract(month from h.created_at)    as created_month,

    -- Header Financials
    h.net_value                         as order_net_value,
    h.currency,

    -- Item Aggregations
    m.total_line_items,
    m.total_quantity_ordered,
    m.total_items_value,
    m.avg_unit_price,
    m.min_unit_price,
    m.max_unit_price,

    -- Derived Metrics (useful for AI/ML features)
    round(m.total_items_value / nullif(m.total_line_items, 0), 2)   as avg_line_item_value,
    round(h.net_value / nullif(m.total_quantity_ordered, 0), 2)     as avg_revenue_per_unit,

    -- Audit
    h.created_by,
    current_timestamp
()                 as dbt_loaded_at

    from sales_headers h
    left join order_item_metrics m
        on h.sales_order_number = m.sales_order_number

)

select *
from final