SELECT

    customer_key,

    customer_id,
    customer_number,

    customer_name,

    COALESCE(customer_group, 'Unassigned') AS customer_group,

    COALESCE(sector, 'Unassigned') AS sector,

    COALESCE(province, 'Unassigned') AS province,

    entity_type,

    site_location,

    website_link,

    tariff_name,

    ipp_name,

    existing_ipp_relation,

    wheeling_type,

    ppa,

    key_opportunities,

    planned_capacity_mw,

    carbon_reduction_targets

FROM {silver.customer}