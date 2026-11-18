SELECT

    c.customer_key,

    c.customer_id,

    c.customer_name,

    c.customer_group,

    c.province,

    c.site_location,

    c.sector,

    c.entity_type,

    c.annual_consumption_gwh,

    c.average_demand_mw,

    c.tariff_name,

    c.existing_ipp_relation,

    c.ipp_name,

    c.wheeling_type,

    c.ppa,

    c.key_opportunities,

    c.planned_capacity_mw,

    c.carbon_reduction_targets,

    e.relationship_manager,

    e.engagement_stage,

    e.opportunity_status,

    e.relationship_strength,

    e.latest_engagement_date,

    e.next_action,

    e.action_owner,

    e.key_risk,

    e.portfolio_offered

FROM {silver.customer} c

LEFT JOIN {silver.engagement} e
       ON e.customer_id = c.customer_id