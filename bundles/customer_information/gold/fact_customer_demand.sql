SELECT
    customer_key,
    annual_consumption_gwh,
    average_demand_mw,
    ROUND(annual_consumption_gwh / 8.76, 2)                     AS implied_demand_mw,
    ROUND(average_demand_mw - annual_consumption_gwh / 8.76, 2) AS demand_gap_mw,
    date('now')                                                 AS snapshot_date
FROM {silver.customer}