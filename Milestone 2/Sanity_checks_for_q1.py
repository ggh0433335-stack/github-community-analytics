import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# connect to database
connection = sqlite3.connect("project_data.db")

#SANITY CHECKS

#1 This just to verify that rows are not empty and numbers make sense (like 2 repositories)
tables = [
    "repositories",
    "pull_requests",
    "contributors",
    "issues",
    "commits"
]

for table in tables:
    query = f"SELECT COUNT(*) AS count FROM {table}"
    result = pd.read_sql_query(query, connection)

    #print(f"{table}:")
    #print(result)
    #print()

#2 This to check if any data is missing, most important that there should 0 missing created_at PR
query1 = """
SELECT
    COUNT(*) AS total_prs,

    SUM(CASE WHEN created_at IS NULL THEN 1 ELSE 0 END)
        AS missing_created_at,

    SUM(CASE WHEN closed_at IS NULL THEN 1 ELSE 0 END)
        AS missing_closed_at,

    SUM(CASE WHEN merged_at IS NULL THEN 1 ELSE 0 END)
        AS missing_merged_at

FROM pull_requests
"""

#print(pd.read_sql_query(query1, connection))

#3 Checks if there is any PR that close before it was created. List should be empty.
query2 = """
SELECT
    id,
    created_at,
    closed_at,

    julianday(closed_at) - julianday(created_at)
        AS duration_days

FROM pull_requests

WHERE closed_at IS NOT NULL
AND julianday(closed_at) - julianday(created_at) < 0
"""

negative_df = pd.read_sql_query(query2, connection)

#print(negative_df)

#4 Checks if merged PRs should are also closed, which should always be the case. 
query3 = """
SELECT COUNT(*) AS suspicious_prs

FROM pull_requests

WHERE merged_at IS NOT NULL
AND closed_at IS NULL
"""

print(pd.read_sql_query(query3, connection))

#5 Duration statistics, shows mean, median, max between two repositories. Median has to be lower than mean. 
query4 = """
SELECT
    r.name AS repository_name,

    julianday(pr.closed_at) - julianday(pr.created_at)
        AS duration_days

FROM pull_requests pr
JOIN repositories r
    ON pr.repo_id = r.id

WHERE pr.closed_at IS NOT NULL
"""

# load data
df = pd.read_sql_query(query4, connection)

# grouped descriptive statistics
stats = (
    df.groupby('repository_name')['duration_days']
      .describe()
)

#print(stats)

#6 
query5 = """SELECT
    r.name AS repository_name,

    COUNT(pr.id) AS total_prs,

    -- open PRs
    SUM(
        CASE
            WHEN pr.closed_at IS NULL
                 AND pr.merged_at IS NULL
            THEN 1
            ELSE 0
        END
    ) AS open_prs,

    -- open PR rate
    ROUND(
        100.0 * SUM(
            CASE
                WHEN pr.closed_at IS NULL
                     AND pr.merged_at IS NULL
                THEN 1
                ELSE 0
            END
        ) / COUNT(pr.id),
        2
    ) AS open_pr_rate_percent

FROM repositories r
JOIN pull_requests pr
    ON r.id = pr.repo_id

GROUP BY r.id, r.name

ORDER BY open_pr_rate_percent DESC;

"""
#print(pd.read_sql_query(query5, connection))