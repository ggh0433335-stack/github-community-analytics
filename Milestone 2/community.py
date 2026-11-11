import sqlite3
import pandas as pd

print("code is running")
db_path = "project_data.db"
start_date = "2010-08-16"
end_date = "2026-3-30"

# Connecting SQL
conn = sqlite3.connect(db_path)

# Mapping done to get the names
repositories_df = pd.read_sql_query("""
    SELECT repositories.id AS repo_id, repositories.name AS full_name, contributors.login AS owner_login 
    FROM repositories
    LEFT JOIN contributors ON repositories.owner_id = contributors.id
""", conn)
repo_map = dict(zip(repositories_df["repo_id"], repositories_df["full_name"]))
repo_owners = dict(zip(repositories_df["repo_id"], repositories_df["owner_login"]))

# Unionising all contributing factors
query = """
SELECT commits.repo_id, contributors.login AS username, commits.committed_at AS contribution_time 
FROM commits
JOIN contributors ON commits.author_id = contributors.id
WHERE contributors.login IS NOT NULL

UNION ALL

SELECT pull_requests.repo_id, contributors.login AS username, pull_requests.created_at AS contribution_time 
FROM pull_requests
JOIN contributors ON pull_requests.contributor_id = contributors.id
WHERE contributors.login IS NOT NULL

UNION ALL

SELECT pull_requests.repo_id, contributors.login AS username, pr_reviews.submitted_at AS contribution_time 
FROM pr_reviews
JOIN pull_requests ON pr_reviews.pr_id = pull_requests.id
JOIN contributors ON pr_reviews.reviewer_id = contributors.id
WHERE contributors.login IS NOT NULL

UNION ALL

SELECT pull_requests.repo_id, contributors.login AS username, pr_comments.created_at AS contribution_time 
FROM pr_comments
JOIN pull_requests ON pr_comments.pr_id = pull_requests.id
JOIN contributors ON pr_comments.contributor_id = contributors.id
WHERE contributors.login IS NOT NULL

UNION ALL

SELECT issues.repo_id, contributors.login AS username, issues.created_at AS contribution_time 
FROM issues
JOIN contributors ON issues.contributor_id = contributors.id
WHERE contributors.login IS NOT NULL

UNION ALL

SELECT issues.repo_id, contributors.login AS username, issue_comments.created_at AS contribution_time 
FROM issue_comments
JOIN issues ON issue_comments.issue_id = issues.id
JOIN contributors ON issue_comments.contributor_id = contributors.id
WHERE contributors.login IS NOT NULL
"""

all_contributions = pd.read_sql_query(query, conn)
conn.close()

# Convert into standard time for python to easily analyse
all_contributions["contribution_time"] = pd.to_datetime(all_contributions["contribution_time"]).dt.tz_localize(None)

# Sort dataframe to group rows by resposit ID, clusters usernames and places contributions from oldest to newest
all_contributions = all_contributions.sort_values(by=["repo_id", "username", "contribution_time"])

# new acoloumn to hold previous contribution
all_contributions["prev_contribution"] = all_contributions.groupby(["repo_id", "username"])["contribution_time"].shift(1)
#calculate time difference between previous contribution and newest contribution
all_contributions["days_since_last"] = (all_contributions["contribution_time"] - all_contributions["prev_contribution"]).dt.days
#check if its above 90 days, if so then returning contributer and placed in newer coloumn
all_contributions["is_returning"] = all_contributions["days_since_last"] >= 90
all_contributions["never_returning"] = all_contributions["days_since_last"] <= 90

all_contributions["first_ever_contribution_date"] = all_contributions.groupby(["repo_id", "username"])["contribution_time"].transform("min")
# 
first_contribution_dates = all_contributions.groupby(["repo_id", "username"])["contribution_time"].min()

# Sset up rules for time, a date includes both the first day and 90th day hence 2nd line after this
start_date_remastered = pd.to_datetime(start_date)
end_date_remastered = pd.to_datetime(end_date + "T23:59:59")

# iterate over every repostrity id, placing its rows into a smaller dataframe called rpo_group
for repo_id, repo_group in all_contributions.groupby("repo_id"):
    #deals with repositrys having no name, CHECK WITH TEAM IF WE WANT THIS, I FORGOT IF WE WANT TO GET RID OF THIS STUFF
    default_name = "repostrity ID: " + str(repo_id)
    repo_name = repo_map.get(repo_id, default_name)
    
    print("_" * 23)
    print("repostrity: " + repo_name)
    print("Timeline: " + start_date + " to " + end_date)
    print("_" * 23)
    
    # Pull only the contributions falling into our main timeframe window
    window_contributions = repo_group[(repo_group["contribution_time"] >= start_date_remastered) & 
                                    (repo_group["contribution_time"] <= end_date_remastered)]
    
    if not window_contributions.empty:
        min_date = window_contributions["contribution_time"].min()
        max_date = window_contributions["contribution_time"].max()
    
        assert min_date >= start_date_remastered, "sanity check failed as contribution found at " + str(min_date) +  "which is before " + str(start_date) 
        assert max_date <= end_date_remastered, "sanity check failed as contribution found at " + str(max_date) + " which is after " + str(end_date)
        #Find returning contributors
        returning_contributions = window_contributions[window_contributions["is_returning"] == True]
        returning_names = list(returning_contributions["username"].unique())
        
        # recognise new contributors
        new_names = []
        active_names = window_contributions["username"].unique()
        for user in active_names:
            global_first_date = first_contribution_dates[(repo_id, user)]
            if global_first_date >= start_date_remastered and global_first_date <= end_date_remastered:
                new_names.append(user)
        
        # Bus factor people identificator
        user_counts = window_contributions.groupby("username").size().reset_index(name="contribution_count")
        group_sorted = user_counts.sort_values(by="contribution_count", ascending=False)
        
        total_contributions = group_sorted["contribution_count"].sum()
        threshold = total_contributions * 0.50
        cumulative_contributions = 0
        bus_factor = 0
        bus_factor_names = []
        
        for x, row in group_sorted.iterrows():
            cumulative_contributions += row["contribution_count"]
            bus_factor += 1
            bus_factor_names.append(row["username"])
            if cumulative_contributions > threshold:
                break
        
        # the results of everything
        print("Total Contributor Count: " + str(len(active_names)))
        print("Total Contributions Analyzed: " + str(total_contributions))
        print("Bus Factor Score: " + str(bus_factor))
        print("Bus People: " + ", ".join(bus_factor_names))
        
        print("Returning Contributors (90+ day absence): " + str(len(returning_names)))
        print("_"*20)

        

        quarter_start = start_date_remastered 
        qcounter = 1
        while quarter_start < end_date_remastered:
            quater_end = quarter_start + pd.Timedelta(days=89, hours=23, minutes=59, seconds=59)
            print( "Quater: " + str(qcounter) )
            print("date start: " + str(quarter_start))
            print("date end: " + str(quater_end))

            window_contributions = repo_group[(repo_group["contribution_time"] >= quarter_start) & 
                                    (repo_group["contribution_time"] <= quater_end)]
            if not window_contributions.empty:
                
                quarter_min = window_contributions["contribution_time"].min()
                quarter_max = window_contributions["contribution_time"].max()
                
                assert quarter_min >= quarter_start, "Sanity check failed at quarter " + str(qcounter) + ". the date failed at" + str(quarter_min) + " which is before" + str(quarter_start)
                assert quarter_max <= quater_end, "Sanity check failed at quarter " + str(qcounter) + ". the date failed at " + str(quarter_max) + "  which is after  " + str(quater_end)
                
                min_date = window_contributions["contribution_time"].min()
                max_date = window_contributions["contribution_time"].max()
    
                assert min_date >= start_date_remastered, "sanity check failed as contribution found at " + str(min_date) +  "which is before " + str(start_date) 
                assert max_date <= end_date_remastered, "sanity check failed as contribution found at " + str(max_date) + " which is after " + str(end_date)
            

                #Find returning contributors
                returning_contributions = window_contributions[window_contributions["is_returning"] == True]
                returning_names = list(returning_contributions["username"].unique())

                # recognise new contributors
                new_names = []
                active_names = window_contributions["username"].unique()
                for user in active_names:
                    global_first_date = first_contribution_dates[(repo_id, user)]
                    if global_first_date >= quarter_start and global_first_date <= quater_end:
                        new_names.append(user)

                # Bus factor people identificator
                user_counts = window_contributions.groupby("username").size().reset_index(name="contribution_count")
                group_sorted = user_counts.sort_values(by="contribution_count", ascending=False)

                total_contributions = group_sorted["contribution_count"].sum()
                threshold = total_contributions * 0.50
                cumulative_contributions = 0
                bus_factor = 0
                bus_factor_names = []
                
                for x, row in group_sorted.iterrows():
                    cumulative_contributions += row["contribution_count"]
                    bus_factor += 1
                    bus_factor_names.append(row["username"])
                    if cumulative_contributions > threshold:
                        break

                print("Total Contributor Count for the quarter: " + str(len(active_names)))
                print("Total Contributions Analyzed for the quarter: " + str(total_contributions))
                print("Bus Factor Score for the quarter: " + str(bus_factor))
                print("Bus People for the quarter: " + ", ".join(bus_factor_names))
                print("New contributors: " + str(len(new_names)))
                print("Returning Contributors (90+ day absence): " + str(len(returning_names)))
                print("_"*20)
            qcounter += 1
            quarter_start += pd.Timedelta(days=90)
                