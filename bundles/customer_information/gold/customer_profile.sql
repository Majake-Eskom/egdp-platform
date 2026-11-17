SELECT

    customer_key,
    customer_id,

    customer_number,

    customer_name,
    customer_group,

    province,
    site_location,

    sector,
    entity_type,

    annual_consumption_gwh,
    average_demand_mw,

    tariff_name,

    existing_ipp_relation,
    ipp_name,

    wheeling_type,
    ppa,

    key_opportunities,
    planned_capacity_mw,

    carbon_reduction_targets,

    website_link

FROM {silver.customer}