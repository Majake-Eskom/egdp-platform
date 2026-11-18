SELECT

    customer_id,

    customer_name,

    customer_group,

    sector,

    province,

    annual_consumption_gwh,

    average_demand_mw,

    planned_capacity_mw,

    key_opportunities,

    carbon_reduction_targets

FROM {silver.customer}

WHERE annual_consumption_gwh IS NOT NULL

ORDER BY annual_consumption_gwh DESC