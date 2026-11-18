SELECT

    SUM(
        CASE
            WHEN relationship_manager IS NULL
                 OR relationship_manager='TBC'
            THEN 1
            ELSE 0
        END
    ) AS missing_relationship_manager,

    SUM(
        CASE
            WHEN action_owner IS NULL
                 OR action_owner='TBC'
            THEN 1
            ELSE 0
        END
    ) AS missing_action_owner,

    SUM(
        CASE
            WHEN engagement_stage IS NULL
            THEN 1
            ELSE 0
        END
    ) AS missing_engagement_stage

FROM {silver.engagement}