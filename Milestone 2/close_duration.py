import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# connect
connection = sqlite3.connect("project_data.db")

# IMPORTANT:
# replace with REAL repository names
repo1 = "repository_name_1"
repo2 = "repository_name_2"

query = """
SELECT
    r.name AS repository_name,
    pr.created_at,

    julianday(pr.closed_at) - julianday(pr.created_at)
        AS close_duration_days

FROM pull_requests pr
JOIN repositories r
    ON pr.repo_id = r.id

WHERE pr.closed_at IS NOT NULL
AND r.name IN ('scikit-learn', 'pandas')
"""

# load data
df = pd.read_sql_query(query, connection)

# DEBUG
print(df.head())

# check repositories loaded
print("\nRepositories found:")
print(df['repository_name'].unique())

# convert dates
df['created_at'] = pd.to_datetime(df['created_at'])

# group by month
df['month'] = df['created_at'].dt.strftime('%Y-%m')

monthly_avg = (
    df.groupby(['month', 'repository_name'])['close_duration_days']
      .mean()
      .reset_index()
)

# DEBUG
print("\nGrouped data:")
print(monthly_avg.head(20))

# plot
plt.figure(figsize=(14, 7))

# create separate line for each repository
for repo_name in monthly_avg['repository_name'].unique():

    repo_data = monthly_avg[
        monthly_avg['repository_name'] == repo_name
    ]

    plt.plot(
        repo_data['month'],
        repo_data['close_duration_days'],
        marker='o',
        linewidth=2,
        label=repo_name
    )

# labels
plt.xlabel("Month")
plt.ylabel("Average PR Close Duration (Days)")
plt.title("Pull Request Close Duration Comparison")

plt.xticks(rotation=45)

# IMPORTANT:
plt.legend()

plt.grid(True)

plt.tight_layout()
plt.show()