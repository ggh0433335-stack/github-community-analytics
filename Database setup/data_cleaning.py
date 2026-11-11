import sqlite3

conn = sqlite3.connect("project_data.db")
cursor = conn.cursor()

# remove bot contributors

cursor.execute("""
DELETE FROM contributors
WHERE LOWER(type) = 'bot'
   OR LOWER(login) LIKE '%[bot]%'
   OR LOWER(login) LIKE '%bot%'
""")

# remove incomplete commits

cursor.execute("""
DELETE FROM commits
WHERE sha IS NULL
   OR repo_id IS NULL
   OR committed_at IS NULL
   OR author_id IS NULL
   OR committer_id IS NULL;
""")

# ensure commits only reference valid contributors
cursor.execute("""
DELETE FROM commits
WHERE author_id NOT IN (SELECT id FROM contributors)
   OR committer_id NOT IN (SELECT id FROM contributors);
""")

# clean pull requests

cursor.execute("""
DELETE FROM pull_requests
WHERE id IS NULL
   OR repo_id IS NULL
   OR state IS NULL
   OR contributor_id IS NULL
   OR created_at IS NULL;
""")

cursor.execute("""
DELETE FROM pull_requests
WHERE contributor_id NOT IN (SELECT id FROM contributors);
""")

# clean issues

cursor.execute("""
DELETE FROM issues
WHERE id IS NULL
   OR repo_id IS NULL
   OR created_at IS NULL
   OR updated_at IS NULL
   OR contributor_id IS NULL;
""")

cursor.execute("""
DELETE FROM issues
WHERE contributor_id NOT IN (SELECT id FROM contributors);
""")

# clean commments (PR and issue)

cursor.execute("""
DELETE FROM pr_comments
WHERE id IS NULL
   OR pr_id IS NULL
   OR contributor_id IS NULL
   OR created_at IS NULL
   OR updated_at IS NULL;
""")

cursor.execute("""
DELETE FROM pr_comments
WHERE contributor_id NOT IN (SELECT id FROM contributors);
""")

cursor.execute("""
DELETE FROM issue_comments
WHERE id IS NULL
   OR issue_id IS NULL
   OR contributor_id IS NULL
   OR created_at IS NULL
   OR updated_at IS NULL;
""")

cursor.execute("""
DELETE FROM issue_comments
WHERE contributor_id NOT IN (SELECT id FROM contributors);
""")

# clean PR reviews

cursor.execute("""
DELETE FROM pr_reviews
WHERE id IS NULL
   OR pr_id IS NULL
   OR submitted_at IS NULL;
""")

cursor.execute("""
DELETE FROM pr_reviews
WHERE reviewer_id IS NOT NULL
  AND reviewer_id NOT IN (SELECT id FROM contributors);
""")

# clean labels

cursor.execute("""
DELETE FROM labels
WHERE id IS NULL
   OR name IS NULL;
""")

cursor.execute("""
DELETE FROM pr_label
WHERE pr_id NOT IN (SELECT id FROM pull_requests)
   OR label_id NOT IN (SELECT id FROM labels);
""")

cursor.execute("""
DELETE FROM issue_label
WHERE issue_id NOT IN (SELECT id FROM issues)
   OR label_id NOT IN (SELECT id FROM labels);
""")

# commit changes

conn.commit()
conn.close()