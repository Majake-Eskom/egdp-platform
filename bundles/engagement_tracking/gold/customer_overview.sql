WITH latest AS (
    SELECT e.*,
           ROW_NUMBER() OVER (
               PARTITION BY e.customer_id
               ORDER BY e.last_engagement_date DESC, e.tracker_id DESC
           ) AS rn
    FROM {silver.engagement} e
)
SELECT
    c.customer_key,
    c.customer_id,
    c.customer_name,
    COALESCE(c.customer_group, 'Unassigned') AS customer_group,
    COALESCE(c.sector, 'Unassigned')         AS sector,
    COALESCE(c.province, 'Unassigned')       AS province,
    c.entity_type,
    c.site_location,
    c.annual_consumption_gwh,
    c.average_demand_mw,
    c.tariff_name,
    c.ipp_name,
    c.wheeling_type,
    c.ppa,
    c.carbon_reduction_targets,
    COALESCE(l.engagement_stage, 'No engagement recorded') AS engagement_stage,
    l.opportunity_status,
    l.portfolio_offered,
    l.relationship_manager,
    l.action_owner,
    l.last_engagement_date,
    l.latest_engagement_summary,
    l.next_action,
    l.next_action_due_date,
    l.key_risk,
    CASE WHEN l.tracker_id IS NULL THEN 'No' ELSE 'Yes' END                 AS has_engagement,
    CASE WHEN l.next_action_due_date < date('now') THEN 'Yes' ELSE 'No' END AS action_overdue
FROM {silver.customer} c
LEFT JOIN latest l ON l.customer_id = c.customer_id AND l.rn = 1
ORDER BY c.customer_name