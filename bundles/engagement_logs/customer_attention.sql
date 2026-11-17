SELECT

    customer_id,

    engagement_stage,

    opportunity_status,

    next_action,

    action_owner,

    key_risk

FROM {silver.engagement}

WHERE

       engagement_stage = 'Awaiting Engagement'

    OR opportunity_status = 'Pending'

    OR next_action_due_date < date('now')