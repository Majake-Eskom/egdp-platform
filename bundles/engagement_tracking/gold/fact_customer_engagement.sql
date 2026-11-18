SELECT

    c.customer_key,

    e.customer_id,

    e.relationship_manager,

    e.action_owner,

    e.engagement_stage,

    e.opportunity_status,

    e.portfolio_offered,

    e.existing_relationship_status,

    e.relationship_strength,

    e.first_engagement_date,

    e.latest_engagement_date,

    e.meeting_notes,

    e.next_action,

    e.next_action_due_date,

    e.key_risk,

    CAST(
        julianday('now') -
        julianday(e.latest_engagement_date)

        AS INTEGER
    ) AS days_since_last_engagement,

    CASE
        WHEN e.next_action_due_date < date('now')
        THEN 1
        ELSE 0
    END AS is_overdue

FROM {silver.engagement} e

LEFT JOIN {silver.customer} c
    ON c.customer_id = e.customer_id