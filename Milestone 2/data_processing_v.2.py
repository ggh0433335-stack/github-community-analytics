import sqlite3
import matplotlib.pyplot as plt

connection = sqlite3.connect('project_data.db')
cursor = connection.cursor()

#query1 shows total PRs, merged PRs, merge rate (percentage), average close time, average merge time).
#time is shown in days
query1 = """
    SELECT
    r.name AS repository_name,

    COUNT(pr.id) AS total_prs,

    SUM(
        CASE
            WHEN pr.merged_at IS NOT NULL THEN 1
            ELSE 0
        END
    ) AS merged_prs,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN pr.merged_at IS NOT NULL THEN 1
                ELSE 0
            END
        ) / COUNT(pr.id),
        2
    ) AS merge_rate_percent,

    ROUND(
        AVG(
            CASE
                WHEN pr.closed_at IS NOT NULL
                THEN julianday(pr.closed_at) - julianday(pr.created_at)
            END
        ),
        2
    ) AS avg_close_days,

    ROUND(
        AVG(
            CASE
                WHEN pr.merged_at IS NOT NULL
                THEN julianday(pr.merged_at) - julianday(pr.created_at)
            END
        ),
        2
    ) AS avg_merge_days

FROM repositories r
JOIN pull_requests pr
    ON r.id = pr.repo_id

GROUP BY r.id, r.name

ORDER BY avg_merge_days ASC;

"""

cursor.execute(query1)
print(cursor.fetchall())

#query2 shows amount of closed but not merged PRs and it's rate
query2 = """
    SELECT
    r.name AS repository_name,

    -- closed but NOT merged
    SUM(
        CASE
            WHEN pr.closed_at IS NOT NULL
                 AND pr.merged_at IS NULL
            THEN 1
            ELSE 0
        END
    ) AS closed_not_merged_prs,

    -- closed without merge rate
    ROUND(
        100.0 * SUM(
            CASE
                WHEN pr.closed_at IS NOT NULL
                     AND pr.merged_at IS NULL
                THEN 1
                ELSE 0
            END
        ) / COUNT(pr.id),
        2
    ) AS closed_not_merged_rate_percent

FROM repositories r
JOIN pull_requests pr
    ON r.id = pr.repo_id

GROUP BY r.id, r.name

ORDER BY closed_not_merged_prs DESC;
"""

cursor.execute(query2)
print(cursor.fetchall())