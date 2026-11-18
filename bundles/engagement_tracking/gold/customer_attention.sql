SELECT

    customer_id,

    engagement_stage,

    opportunity_status,

    next_action,

    action_owner,

    key_risk,

    next_action_due_date,

    CASE
        WHEN next_action_due_date < date('now')
        THEN 'Overdue Action'

        WHEN engagement_stage = 'Awaiting Engagement'
        THEN 'Awaiting Engagement'

        WHEN opportunity_status = 'Pending'
        THEN 'Pending Opportunity'

        ELSE 'Attention Required'
    END AS attention_reason

FROM {silver.engagement}

WHERE

       engagement_stage = 'Awaiting Engagement'

    OR opportunity_status = 'Pending'

    OR next_action_due_date < date('now')