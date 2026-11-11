import json
from datetime import datetime
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt

# function to count total amount of contributors
def count_contributors(variable, contributor, name) -> None:
    """
    Counts the total amount of contributors
    :param variable: the variable that will be iterated over
    :param contributor: the str representation of how a contributor is identified 
    :param name: name of repository
    """

    if variable[contributor] != None and variable[contributor]['id'] not in unique_contributors[name]:
        unique_contributors[name].append(variable[contributor]['id'])

# function to find all the updated issues
# !!!HAVE TO EDIT THE WAY TO FIND INTERVALS AND DISPLAY GRAPH!!!
    
def find_issue_updates(variable, name) -> None:
    """
    Finds all updated issues
    :param variable: variable holding the data
    :param name: repository name
    """
    issue_updates[name].append(datetime.fromisoformat(variable['updated_at']))

# function to find all the review comment (will be used to find the average)

def count_review_comments(variable, name) -> None:
    """
    Finds amount of review comments per pull request
    :param variable: variable holding the data
    """

    review_comments[name].append(variable['review_comments_count'])

# function to find distinct commits with their respective date

def find_commits(variable, name) -> None:
    """
    Finds commits and appends them along with their date to a 2D list
    :param variable: variable holding the data
    """

    commits_per_week[name].append([variable['sha'],variable['committed_at']])

# function to find all the issue comments

def count_issue_comments(variable, name) -> None:
    """
    Counts the total amount of comments per issue
    :param variable: vairable being iterated over
    """ 
    
    comment_count: int = 0
    for comment in variable['comments']:
        comment_count += 1

    total_issue_comments[name].append(comment_count)

unique_contributors: dict[list[str]] = {'scikit-learn' : [], 'pandas' : []}
issue_updates: dict[list[datetime]] = {'scikit-learn' : [], 'pandas' : []}
review_comments: dict[list[int]] = {'scikit-learn' : [], 'pandas' : []}
commits_per_week: dict[list[str, datetime]] = {'scikit-learn' : [], 'pandas' : []}
total_issue_comments: dict[list[int]] = {'scikit-learn' : [], 'pandas' : []}
months: list[str] = []

with open('Milestone 1/big_github_data_2025_readable.json') as file:
    data = json.load(file)

    # SCIKIT-LEARN

    # variables scikit-learn

    for obj in data:   
        if obj['name'] == 'scikit-learn':

            commits = obj['commits']   
            for commit in commits:
                count_contributors(commit,'author',obj['name']) 
                count_contributors(commit,'committer',obj['name'])
                find_commits(commit,obj['name'])

            pull_requests = obj['pull_requests']
            for pull_request in pull_requests:
                count_contributors(pull_request,'user',obj['name'])
                count_review_comments(pull_request,obj['name'])
            
            issues = obj['issues']
            for issue in issues:
                count_contributors(issue,'user',obj['name'])
                find_issue_updates(issue,obj['name'])
                count_issue_comments(issue,obj['name'])
            
            print(f"Total number of contributors in {obj['name']}: {len(unique_contributors[obj['name']])}")
            print(f"Total number of issue updates in {obj['name']}: {len(issue_updates[obj['name']])}")
            print(f"Total number of review comments (pull requests) in {obj['name']}: {len(review_comments[obj['name']])}")
            print(f"Total number of commits in {obj['name']}: {len(commits_per_week[obj['name']])}")
            print(f"Total number of issue comments in {obj['name']}: {len(total_issue_comments[obj['name']])}")

    # PANDAS

    for obj in data:   
        if obj['name'] == 'pandas':

            commits = obj['commits']   
            for commit in commits:
                count_contributors(commit,'author',obj['name']) 
                count_contributors(commit,'committer',obj['name'])
                find_commits(commit,obj['name'])

            pull_requests = obj['pull_requests']
            for pull_request in pull_requests:
                count_contributors(pull_request,'user',obj['name'])
                count_review_comments(pull_request,obj['name'])
            
            issues = obj['issues']
            for issue in issues:
                count_contributors(issue,'user',obj['name'])
                find_issue_updates(issue,obj['name'])
                count_issue_comments(issue,obj['name'])
            
            print(f"\nTotal number of contributors in {obj['name']}: {len(unique_contributors[obj['name']])}")
            print(f"Total number of issue updates in {obj['name']}: {len(issue_updates[obj['name']])}")
            print(f"Total number of review comments (pull requests) in {obj['name']}: {len(review_comments[obj['name']])}")
            print(f"Total number of commits in {obj['name']}: {len(commits_per_week[obj['name']])}")
            print(f"Total number of issue comments in {obj['name']}: {len(total_issue_comments[obj['name']])}")

# order the dates 
issue_updates['scikit-learn'] = sorted(issue_updates['scikit-learn'])
issue_updates['pandas'] = sorted(issue_updates['pandas'])

# scikit-learn
df_sklearn = pd.DataFrame({'date': issue_updates['scikit-learn']})
df_sklearn['date'] = pd.to_datetime(df_sklearn['date'])
df_grouped_sklearn = df_sklearn.groupby(df_sklearn['date'].dt.date).size().reset_index(name='count')
df_grouped_sklearn['date'] = pd.to_datetime(df_grouped_sklearn['date'])

# pandas
df_pandas = pd.DataFrame({'date': issue_updates['pandas']})
df_pandas['date'] = pd.to_datetime(df_pandas['date'])
df_grouped_pandas = df_pandas.groupby(df_pandas['date'].dt.date).size().reset_index(name='count')
df_grouped_pandas['date'] = pd.to_datetime(df_grouped_pandas['date'])

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(df_grouped_sklearn['date'], df_grouped_sklearn['count'], label='scikit-learn')
ax.plot(df_grouped_pandas['date'], df_grouped_pandas['count'], color='red', label='pandas')

ax.set_xlabel('Date')
ax.set_ylabel('Number of Issue Updates')
ax.set_title('Issue Updates Over Time')
ax.legend()
plt.tight_layout()
plt.show()