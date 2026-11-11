import sqlite3
import json

connection = sqlite3.connect('project_data.db')
cursor = connection.cursor()

contributors = """
CREATE TABLE IF NOT EXISTS contributors (
    id          INTEGER PRIMARY KEY,
    login       TEXT,
    type        TEXT,
    site_admin  INTEGER
)"""
cursor.execute(contributors)

repositories = """
CREATE TABLE IF NOT EXISTS repositories (
    id                  INTEGER PRIMARY KEY,
    name                TEXT,
    created_at          TEXT,
    updated_at          TEXT,
    owner_id            INTEGER,
    FOREIGN KEY (owner_id) REFERENCES contributors(id)
)"""
cursor.execute(repositories)

commits = """
CREATE TABLE IF NOT EXISTS commits (
    sha             TEXT PRIMARY KEY,
    repo_id         INTEGER,
    committed_at    TEXT,
    author_id       INTEGER,
    committer_id    INTEGER,
    FOREIGN KEY (repo_id)       REFERENCES repositories(id),
    FOREIGN KEY (author_id)     REFERENCES contributors(id),
    FOREIGN KEY (committer_id)  REFERENCES contributors(id)
)"""
cursor.execute(commits)

labels = """
CREATE TABLE IF NOT EXISTS labels (
    id          INTEGER PRIMARY KEY,
    name        TEXT,
    description TEXT
)"""
cursor.execute(labels)

pull_requests = """
CREATE TABLE IF NOT EXISTS pull_requests (
    id                      INTEGER PRIMARY KEY,
    repo_id                 INTEGER,
    state                   TEXT,
    contributor_id          INTEGER,
    created_at              TEXT,
    closed_at               TEXT,
    merged_at               TEXT,  
    FOREIGN KEY (repo_id)           REFERENCES repositories(id),
    FOREIGN KEY (contributor_id)    REFERENCES contributors(id)
)"""
cursor.execute(pull_requests)

issues = """
CREATE TABLE IF NOT EXISTS issues (
    id              INTEGER PRIMARY KEY,
    repo_id         INTEGER,
    created_at      TEXT,
    updated_at      TEXT,
    contributor_id  INTEGER,
    FOREIGN KEY (repo_id)           REFERENCES repositories(id),
    FOREIGN KEY (contributor_id)    REFERENCES contributors(id)
)"""
cursor.execute(issues)

pr_label = """
CREATE TABLE IF NOT EXISTS pr_label (
    pr_id       INTEGER,
    label_id    INTEGER,
    PRIMARY KEY (pr_id, label_id),
    FOREIGN KEY (pr_id)     REFERENCES pull_requests(id),
    FOREIGN KEY (label_id)  REFERENCES labels(id)
)"""
cursor.execute(pr_label)

pr_comments = """
CREATE TABLE IF NOT EXISTS pr_comments (
    id              INTEGER PRIMARY KEY,
    pr_id           INTEGER,
    contributor_id  INTEGER,
    created_at      TEXT,
    updated_at      TEXT,
    FOREIGN KEY (pr_id)          REFERENCES pull_requests(id),
    FOREIGN KEY (contributor_id) REFERENCES contributors(id)
)"""

cursor.execute(pr_comments)

pr_reviews = """
CREATE TABLE IF NOT EXISTS pr_reviews (
    id              INTEGER PRIMARY KEY,
    pr_id           INTEGER,
    reviewer_id     INTEGER,
    submitted_at    TEXT,
    FOREIGN KEY (pr_id)         REFERENCES pull_requests(id),
    FOREIGN KEY (reviewer_id)   REFERENCES contributors(id)
)"""

cursor.execute(pr_reviews)

issue_label = """
CREATE TABLE IF NOT EXISTS issue_label (
    issue_id    INTEGER,
    label_id    INTEGER,
    PRIMARY KEY (issue_id, label_id),
    FOREIGN KEY (issue_id)  REFERENCES issues(id),
    FOREIGN KEY (label_id)  REFERENCES labels(id)
)"""

cursor.execute(issue_label)

issue_comments = """
CREATE TABLE IF NOT EXISTS issue_comments (
    id      INTEGER PRIMARY KEY,
    issue_id        INTEGER,
    contributor_id  INTEGER,
    created_at      TEXT,
    updated_at      TEXT,
    FOREIGN KEY (issue_id)       REFERENCES issues(id),
    FOREIGN KEY (contributor_id) REFERENCES contributors(id)
)"""

cursor.execute(issue_comments)

with open('big_github_data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

    for obj in data:
            
            # OWNER

            owner = obj["owner"]

            cursor.execute(
            "INSERT OR IGNORE INTO contributors VALUES (?, ?, ?, ?)",
            (
                owner['id'], 
                owner['login'], 
                owner['type'], 
                owner['site_admin']
            ))

            # REPOSITORY

            cursor.execute(
            "INSERT OR IGNORE INTO repositories VALUES (?, ?, ?, ?, ?)",
            (
                obj['id'], 
                obj['name'], 
                obj['created_at'], 
                obj['updated_at'], 
                obj['owner']['id']
            ))

            # COMMITS

            for commit in obj['commits'] :
                
                # loads the contributors (author) of the commit

                if commit['author'] is not None:
                    author_id = commit['author']['id']
                    cursor.execute(
                        "INSERT OR IGNORE INTO contributors VALUES (?, ?, ?, ?)",
                        (
                            commit['author']['id'],
                            commit['author']['login'],
                            commit['author']['type'],
                            commit['author']['site_admin']
                        ))

                # loads the contributors (committer) of the commit

                if commit['committer'] is not None:
                    committer_id = commit['committer']['id']
                    cursor.execute(
                        "INSERT OR IGNORE INTO contributors VALUES (?, ?, ?, ?)",
                        (
                            commit['committer']['id'],
                            commit['committer']['login'],
                            commit['committer']['type'],
                            commit['committer']['site_admin']
                        ))  

                # loads the commits

                cursor.execute(
                """INSERT OR IGNORE INTO commits (sha, repo_id, committed_at, author_id, committer_id)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    commit['sha'],
                    obj['id'],
                    commit['committed_at'],
                    author_id,
                    committer_id
                ))

            # PULL REQUESTS
                        
            for pull_request in obj['pull_requests']:

                # loads the contributors of the pull requests

                user = pull_request['user']
                cursor.execute(
                    "INSERT OR IGNORE INTO contributors VALUES (?, ?, ?, ?)",
                    (
                        user['id'], 
                        user['login'], 
                        user['type'], 
                        user['site_admin']
                    ))
                
                # loads pull requests

                cursor.execute(
                """INSERT OR IGNORE INTO pull_requests (id, repo_id, state, contributor_id, created_at, closed_at, merged_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    pull_request['id'],
                    obj['id'],
                    pull_request['state'],
                    user['id'],
                    pull_request['created_at'],
                    pull_request['closed_at'],
                    pull_request['merged_at']
                ))
                
                # PULL REQUEST LABELS

                for label in pull_request['labels']:

                    # loads general label

                    cursor.execute(
                    "INSERT OR IGNORE INTO labels VALUES (?, ?, ?)",
                    (
                        label['id'], 
                        label['name'],
                        label['description']
                    ))                    
                    
                    # loads specific pull request label id's

                    cursor.execute(
                    "INSERT OR IGNORE INTO pr_label VALUES (?, ?)",
                    (
                        pull_request['id'], 
                        label['id']
                    ))
                
                # PULL REQUEST COMMENTS

                for comment in pull_request['comments']:

                    # loads pull request comments
                    
                    cursor.execute(
                    "INSERT OR IGNORE INTO pr_comments VALUES (?, ?, ?, ?, ?)",
                    (
                        comment['id'],
                        pull_request['id'],
                        comment['user']['id'],
                        comment['created_at'],
                        comment['updated_at']
                    ))

                # PULL REQUEST REVIEWS

                for review in pull_request['reviews']:

                    # loads pull request reviews
                    reviewer_id = None

                    if review['user'] is not None:
                        reviewer_id = review['user']['id']

                        cursor.execute(
                            "INSERT OR IGNORE INTO contributors VALUES (?, ?, ?, ?)",
                            (
                                review['user']['id'],
                                review['user']['login'],
                                review['user']['type'],
                                review['user']['site_admin']
                            ))

                    # loads the contributors of pull request review

                    cursor.execute(
                        "INSERT OR IGNORE INTO pr_reviews VALUES (?, ?, ?, ?)",
                        (
                            review['id'],
                            pull_request['id'],
                            reviewer_id,
                            review['submitted_at']
                        ))

            # ISSUES

            for issue in obj['issues']:
                    
                # loads the contributors of issues

                user = issue['user']
                cursor.execute(
                "INSERT OR IGNORE INTO contributors VALUES (?, ?, ?, ?)",
                (
                    user['id'], 
                    user['login'], 
                    user['type'], 
                    user['site_admin']
                ))

                # loads issues

                cursor.execute(
                """INSERT OR IGNORE INTO issues (id, repo_id, created_at, updated_at, contributor_id)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    issue['id'],
                    obj['id'],
                    issue['created_at'],
                    issue['updated_at'],
                    user['id']
                ))

                # ISSUES LABELS

                for label in issue['labels']:

                    # loads general label

                    cursor.execute(
                    "INSERT OR IGNORE INTO labels VALUES (?, ?, ?)",
                    (
                        label['id'], 
                        label['name'],
                        label['description']
                    ))

                    # loads specific issue label id's

                    cursor.execute(
                    "INSERT OR IGNORE INTO issue_label VALUES (?, ?)",
                    (
                        issue['id'], 
                        label['id']
                    ))

                # ISSUES COMMENTS

                for comment in issue['comments']:
                    
                    # loads issue comments

                    cursor.execute(
                    "INSERT OR IGNORE INTO issue_comments VALUES (?, ?, ?, ?, ?)",
                    (
                        comment['id'],
                        issue['id'],
                        comment['user']['id'],
                        comment['created_at'],
                        comment['updated_at']
                    ))

connection.commit()
connection.close()