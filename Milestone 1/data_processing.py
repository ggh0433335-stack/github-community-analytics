import sqlite3
import matplotlib.pyplot as plt

connection = sqlite3.connect('project_data.db')
cursor = connection.cursor()

#                                               == Milestone I Graphs and Data ==
#                                   works with small data 2025, doesnt work with new database


# number of commits - counts the number of commits per repo
query_num_commits = """
    SELECT r.name, COUNT(DISTINCT i.sha) AS commit_count
    FROM commits i
    JOIN repositories r ON i.repo_id = r.id
    GROUP BY r.name
"""

cursor.execute(query_num_commits)
#print(cursor.fetchall())
      
# number of issues - counts the number of issues per repo
query_num_issues = """
    SELECT r.name, COUNT(DISTINCT i.id) AS issue_count
    FROM issues i
    JOIN repositories r ON i.repo_id = r.id
    GROUP BY r.name
"""

cursor.execute(query_num_issues)
#print(cursor.fetchall())

# query for label name graph
# query counts the num of each label name (frequency of each name) for each repo for merged or closed PRs
query_each_label_num = """
SELECT r.name AS repo_name, l.name AS label_name, COUNT(*) AS frequency
FROM (

    SELECT pr.repo_id, pl.label_id
    FROM pr_label pl
    JOIN pull_requests pr ON pl.pr_id = pr.id
    WHERE pr.merged_at IS NOT NULL
       OR pr.closed_at IS NOT NULL

) AS t

JOIN repositories r ON t.repo_id = r.id
JOIN labels l ON t.label_id = l.id

GROUP BY r.name, l.name
ORDER BY r.name, frequency DESC;
"""

cursor.execute(query_each_label_num)
label_names = cursor.fetchall()
print(label_names)

#lists set up for graph
pandas_label: list = []
scikitlearn_label: list = []

for label in label_names:
    if label[0] == 'pandas':
        pandas_label.append(label)
    elif label[0] == 'scikit-learn':
        scikitlearn_label.append(label)

pandas_top_five = [pandas_label[0],
                   pandas_label[1],
                   pandas_label[2],
                   pandas_label[3],
                   pandas_label[4],]        
    
scikitlearn_top_five = [scikitlearn_label[0],
                   scikitlearn_label[1],
                   scikitlearn_label[2],
                   scikitlearn_label[3],
                   scikitlearn_label[4],]

pandas_label_freq: list = []
scikitlearn_label_freq: list = []

pandas_label_name: list = []
scikitlearn_label_name: list = []

for label_tuple in pandas_top_five:
    pandas_label_name.append(label_tuple[1])
    pandas_label_freq.append(label_tuple[2])

for label_tuple in scikitlearn_top_five:
    scikitlearn_label_name.append(label_tuple[1])
    scikitlearn_label_freq.append(label_tuple[2])   

# -- pandas graph --
#plt.figure(figsize=(7, 5))
#plt.barh(pandas_label_name, pandas_label_freq)

#plt.xlabel("Number")
#plt.ylabel("Label")
#plt.title("Top 5 Labels of Pandas")

#plt.gca().invert_yaxis()
#plt.tight_layout()
#plt.show()

# -- scikitlearn graph --
#plt.figure(figsize=(8, 5))
#plt.barh(scikitlearn_label_name, scikitlearn_label_freq)

#plt.xlabel("Number")
#plt.ylabel("Label")
#plt.title("Top 5 Labels of Scikitlearn")

#plt.gca().invert_yaxis()
#plt.tight_layout()
#plt.show()

#num of labels named bug(s)
query = """
    SELECT r.name, COUNT(DISTINCT i.id) AS bug_issue_count
    FROM issues i
    JOIN issue_label il ON i.id = il.issue_id
    JOIN labels l ON il.label_id = l.id
    JOIN repositories r ON i.repo_id = r.id
    WHERE LOWER(l.name) IN ('bug', 'bugs')
    GROUP BY r.name
"""

cursor.execute(query)
#print(cursor.fetchall())

#plot for number of PRs
#query for merged, closed and left open PRs
query = """
    SELECT 
        r.name,

        COUNT(DISTINCT CASE 
            WHEN pr.merged_at IS NOT NULL 
            THEN pr.id 
        END) AS merged_prs,

        COUNT(DISTINCT CASE 
            WHEN pr.state = 'closed' 
                 AND pr.merged_at IS NULL 
            THEN pr.id 
        END) AS closed_not_merged_prs,

        COUNT(DISTINCT CASE 
            WHEN pr.state = 'open' 
            THEN pr.id 
        END) AS open_prs

    FROM pull_requests pr
    JOIN repositories r ON pr.repo_id = r.id

    GROUP BY r.name
"""

cursor.execute(query)

repos: list = []
merged: list = []
closed: list = []
left_open: list = []

for row in cursor.fetchall():
    repos.append(row[0])
    merged.append(row[1])
    closed.append(row[2])
    left_open.append(row[3])

#x = range(2)

#plt.bar(x, merged, label="Merged")
#plt.bar(x, closed, bottom=merged, label="Closed Not Merged")

#bottom_open = []
#for i in range(len(merged)):
    #bottom_open.append(merged[i] + closed[i])

#plt.bar(x, left_open, bottom=bottom_open, label="Open")

#plt.xticks(x, repos)
#plt.ylabel("Number of Pull Requests")
#plt.title("Pull Request Status by Repository")
#plt.legend()

#plt.show()

#num of contributors = PR authors, PR commenters, reviewers, commit authors/committers, issue authors and issue commenters
query = """
SELECT r.name, COUNT(DISTINCT contributor_id) AS total_contributors
FROM (

    -- repository owners
    SELECT r.id AS repo_id, r.owner_id AS contributor_id
    FROM repositories r

    UNION

    -- commit authors
    SELECT c.repo_id, c.author_id AS contributor_id
    FROM commits c

    UNION

    -- commit committers
    SELECT c.repo_id, c.committer_id
    FROM commits c

    UNION

    -- PR authors
    SELECT pr.repo_id, pr.contributor_id
    FROM pull_requests pr

    UNION

    -- PR commenters
    SELECT pr.repo_id, pc.contributor_id
    FROM pr_comments pc
    JOIN pull_requests pr
    ON pc.pr_id = pr.id

    UNION

    -- PR reviewers
    SELECT pr.repo_id, prr.reviewer_id
    FROM pr_reviews prr
    JOIN pull_requests pr
    ON prr.pr_id = pr.id

    UNION

    -- issue authors
    SELECT i.repo_id, i.contributor_id
    FROM issues i

    UNION

    -- issue commenters
    SELECT i.repo_id, ic.contributor_id
    FROM issue_comments ic
    JOIN issues i
    ON ic.issue_id = i.id

) AS all_contributors

JOIN repositories r
ON all_contributors.repo_id = r.id

WHERE contributor_id IS NOT NULL

GROUP BY r.name
"""

cursor.execute(query)
print(cursor.fetchall())

#query for the graph of contributor number over time
query_overtime_cont = """
SELECT r.name, activity_date, contributor_id
FROM (

    SELECT c.repo_id, c.committed_at AS activity_date, c.author_id AS contributor_id
    FROM commits c

    UNION

    SELECT c.repo_id, c.committed_at, c.committer_id
    FROM commits c

    UNION

    SELECT pr.repo_id, pr.created_at, pr.contributor_id
    FROM pull_requests pr

    UNION

    SELECT pr.repo_id, pc.created_at, pc.contributor_id
    FROM pr_comments pc
    JOIN pull_requests pr
    ON pc.pr_id = pr.id

    UNION

    SELECT pr.repo_id, prr.submitted_at, prr.reviewer_id
    FROM pr_reviews prr
    JOIN pull_requests pr
    ON prr.pr_id = pr.id

    UNION

    SELECT i.repo_id, i.created_at, i.contributor_id
    FROM issues i

    UNION

    SELECT i.repo_id, ic.created_at, ic.contributor_id
    FROM issue_comments ic
    JOIN issues i
    ON ic.issue_id = i.id

) AS all_contributors

JOIN repositories r
ON all_contributors.repo_id = r.id

WHERE contributor_id IS NOT NULL

ORDER BY activity_date
"""

cursor.execute(query_overtime_cont)
rows = cursor.fetchall()

pandas_seen = set()
sklearn_seen = set()

pandas_dates = []
pandas_totals = []

sklearn_dates = []
sklearn_totals = []

for repo, date, contributor in rows:

    date = date[:10]

    if repo == "pandas":

        pandas_seen.add(contributor)
        pandas_dates.append(date)
        pandas_totals.append(len(pandas_seen))

    elif repo == "scikit-learn":

        sklearn_seen.add(contributor)
        sklearn_dates.append(date)
        sklearn_totals.append(len(sklearn_seen))

x_pandas = list(range(len(pandas_totals)))
x_sklearn = list(range(len(sklearn_totals)))

#plt.figure(figsize=(8, 6))

#plt.plot(x_pandas, pandas_totals, label="pandas")
#plt.plot(x_sklearn, sklearn_totals, label="scikit-learn")

#plt.xlabel("Date")
#plt.ylabel("Contributor Number")
#plt.title("Contributor Number Over Time")

#plt.xticks(x_pandas[::2500], pandas_dates[::2500], rotation=45)

#plt.legend()
#plt.tight_layout()
#plt.show()