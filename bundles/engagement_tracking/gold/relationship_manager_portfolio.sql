SELECT

    relationship_manager,

    COUNT(*) AS total_customers,

    SUM(
        CASE
            WHEN opportunity_status='Active'
            THEN 1
            ELSE 0
        END
    ) AS active_customers,

    SUM(
        CASE
            WHEN opportunity_status='In Progress'
            THEN 1
            ELSE 0
        END
    ) AS in_progress_customers,

    SUM(
        CASE
            WHEN opportunity_status='Pending'
            THEN 1
            ELSE 0
        END
    ) AS pending_customers

FROM {silver.engagement}

GROUP BY relationship_manager

ORDER BY total_customers DESC