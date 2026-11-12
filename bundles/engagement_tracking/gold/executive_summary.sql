SELECT
    (SELECT COUNT(*) FROM {silver.customer})                       AS customers,
    (SELECT COUNT(DISTINCT sector) FROM {silver.customer})         AS sectors,
    (SELECT ROUND(SUM(annual_consumption_gwh), 2) FROM {silver.customer})
                                                                   AS total_annual_consumption_gwh,
    (SELECT ROUND(SUM(average_demand_mw), 2) FROM {silver.customer})
                                                                   AS total_average_demand_mw,
    (SELECT COUNT(*) FROM {silver.engagement})                     AS engagements,
    (SELECT COUNT(*) FROM {silver.engagement}
      WHERE next_action_due_date < date('now'))                    AS overdue_actions,
    (SELECT COUNT(*) FROM {silver.customer} c
      WHERE NOT EXISTS (SELECT 1 FROM {silver.engagement} e
                        WHERE e.customer_id = c.customer_id))      AS customers_without_engagement,
    date('now')                                                    AS as_of_date