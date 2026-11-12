SELECT
    e.engagement_key,
    c.customer_key,
    e.tracker_id,
    e.engagement_stage,
    e.opportunity_status,
    e.portfolio_offered,
    e.relationship_manager,
    e.action_owner,
    e.existing_relationship_status,
    e.relationship_strength,
    e.first_engagement_date,
    e.last_engagement_date,
    e.latest_engagement_summary,
    e.next_action,
    e.next_action_due_date,
    e.key_risk,
    CAST(julianday('now') - julianday(e.last_engagement_date) AS INTEGER)
        AS days_since_last_engagement,
    CASE WHEN e.next_action_due_date < date('now') THEN 1 ELSE 0 END AS is_overdue,
    CASE WHEN e.next_action_due_date < date('now')
         THEN CAST(julianday('now') - julianday(e.next_action_due_date) AS INTEGER)
    END AS days_overdue,
    CASE WHEN julianday('now') - julianday(e.last_engagement_date) > 30
         THEN 1 ELSE 0 END AS is_stale
FROM {silver.engagement} e
LEFT JOIN {silver.customer} c ON c.customer_id = e.customer_id