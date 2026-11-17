SELECT

    relationship_manager,

    COUNT(*) AS customers,

    SUM(
        CASE
            WHEN opportunity_status='Active'
            THEN 1
            ELSE 0
        END
    ) AS active_customers,

    SUM(
        CASE
            WHEN opportunity_status='Pending'
            THEN 1
            ELSE 0
        END
    ) AS pending_customers

FROM {silver.engagement}

GROUP BY relationship_manager