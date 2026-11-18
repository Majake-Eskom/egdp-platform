SELECT

    customer_id,

    customer_name,

    customer_group,

    sector,

    province,

    CASE
        WHEN has_engagement = 'Yes'
        THEN 'Engaged'
        ELSE 'Not Engaged'
    END AS engagement_coverage

FROM {gold.customer_overview}