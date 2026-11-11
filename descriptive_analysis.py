import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import calendar

# formatting from 'Storytelling with Data'
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.titlesize'] = 16
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['grid.color'] = '#e0e0e0'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.edgecolor'] = '#cccccc'
plt.rcParams['axes.spines.top'] = False
plt.rcParams['axes.spines.right'] = False

def get_dates(prompt):
    while True:
        search_date = input(f'What {prompt} do you want to check? (YYYY,MM) ')
        try:
            parts = search_date.strip().split(',')
            if len(parts) != 2:
                raise ValueError("Expected 3 parts")
            
            search_year, month = int(parts[0]), int(parts[1])

            if not (1 <= month <= 12):
                raise ValueError("Month must be 1–12")
            if not (2010 <= search_year <= 2025):
                raise ValueError("Year must be 2010 and before 2026 (data starts August 2010 and ends December 2025)")

            if prompt == 'end date':
                last_day = calendar.monthrange(search_year, month)[1]
                return f"{search_year}-{month:02d}-{last_day:02d}"
            else:
                return f"{search_year}-{month:02d}-01"

        except (ValueError, AttributeError) as error:
            print(f"  Invalid format: {error}. Please enter as 'YYYY,MM' (e.g. 2016,03)\n")


# starting from august 2010
db_path = "project_data.db"

def get_connection():
    return sqlite3.connect(db_path)

# austeja's code
def analyze_pr_metrics_detailed(start_date,end_date):
    f"""
    Queries total PRs, merge rates, rejection rates, lifespans in days, 
    filtered by standard {start_date} and {end_date} horizons.
    Calculates MEDIAN lifespans to prevent outlier distortion,
    and incorporates the change request closure Ratio (RQ1).
    """
    conn = get_connection()
    end_date_extended = end_date + "T23:59:59"

    # 1. query the raw granular PR metrics and individual lifespans
    query_raw_prs = """
    SELECT 
        r.name AS repository_name,
        pr.id AS pr_id,
        pr.merged_at,
        pr.closed_at,
        CASE WHEN pr.closed_at IS NOT NULL THEN julianday(pr.closed_at) - julianday(pr.created_at) END AS close_days,
        CASE WHEN pr.merged_at IS NOT NULL THEN julianday(pr.merged_at) - julianday(pr.created_at) END AS merge_days
    FROM repositories r
    JOIN pull_requests pr ON r.id = pr.repo_id
    WHERE pr.created_at >= ? AND pr.created_at <= ?
    """
    df_raw = pd.read_sql_query(query_raw_prs, conn, params=(start_date, end_date_extended))

    # 2. query the high-level summary components needed for the CHAOSS closure ratio
    query_backlog = """
    SELECT 
        r.name AS repository_name,
        COUNT(pr.id) AS total_prs,
        SUM(CASE WHEN pr.merged_at IS NOT NULL THEN 1 ELSE 0 END) AS merged_prs,
        SUM(CASE WHEN pr.closed_at IS NOT NULL AND pr.merged_at IS NULL THEN 1 ELSE 0 END) AS closed_not_merged_prs,
        SUM(CASE WHEN pr.closed_at IS NOT NULL THEN 1 ELSE 0 END) AS total_closed_actions,
        SUM(CASE WHEN pr.closed_at IS NULL THEN 1 ELSE 0 END) AS total_open_backlog
    FROM repositories r
    JOIN pull_requests pr ON r.id = pr.repo_id
    WHERE pr.created_at >= ? AND pr.created_at <= ?
    GROUP BY r.id, r.name
    """
    df_backlog = pd.read_sql_query(query_backlog, conn, params=(start_date, end_date_extended))
    conn.close()

    # 3. use pandas to group by repository and extract the true median values
    df_medians = df_raw.groupby('repository_name').agg({
        'close_days': 'median',
        'merge_days': 'median'
    }).reset_index()
    
    # rename columns to clearly state they are medians
    df_medians.columns = ['repository_name', 'median_close_days', 'median_merge_days']

    # 4. merge the components together and construct final percentage distributions
    df_final = pd.merge(df_backlog, df_medians, on='repository_name')
    
    df_final['merge_rate_percent'] = (100.0 * df_final['merged_prs'] / df_final['total_prs']).round(2)
    df_final['closed_not_merged_rate_percent'] = (100.0 * df_final['closed_not_merged_prs'] / df_final['total_prs']).round(2)
    df_final['closure_ratio'] = (df_final['total_closed_actions'] / (df_final['total_open_backlog'] + 1)).round(2)
    
    # round the medians to 2 decimal places
    df_final['median_close_days'] = df_final['median_close_days'].round(2)
    df_final['median_merge_days'] = df_final['median_merge_days'].round(2)

    # reorder columns to be sorted by velocity
    column_order = [
        'repository_name', 'total_prs', 'merged_prs', 'merge_rate_percent',
        'closed_not_merged_prs', 'closed_not_merged_rate_percent',
        'median_close_days', 'median_merge_days', 
        'total_closed_actions', 'total_open_backlog', 'closure_ratio'
    ]
    df_final = df_final[column_order].sort_values(by='median_merge_days', ascending=True)

    return df_final

def analyze_ecosystem_community_dynamics(start_date, end_date):
    """
    unionizes all contribution factors (commits, prs, reviews, issues, comments) from project_data.db
    calculates bus factor metrics, prints rolling windows, handles 90-day reactivations,
    and explicitly records the Contributor Absence Footprint Index (Churn), RQ2
    """
    conn = get_connection()
    
    # fetch repository mapping names matching new inner schema
    repositories_df = pd.read_sql_query("""
        SELECT repositories.id AS repo_id, repositories.name AS full_name 
        FROM repositories
    """, conn)
    repo_map = dict(zip(repositories_df["repo_id"], repositories_df["full_name"]))
    
    # synchronized join schema using contributors table across endpoints
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
    
    # print("Unionizing repository lifecycle records")
    all_contributions = pd.read_sql_query(query, conn)
    conn.close()
    
    # process analytical timestamps safely
    all_contributions["contribution_time"] = pd.to_datetime(all_contributions["contribution_time"]).dt.tz_localize(None)
    all_contributions = all_contributions.sort_values(by=["repo_id", "username", "contribution_time"])
    
    # calculate intervals for 90-day returning deltas
    all_contributions["prev_contribution"] = all_contributions.groupby(["repo_id", "username"])["contribution_time"].shift(1)
    all_contributions["days_since_last"] = (all_contributions["contribution_time"] - all_contributions["prev_contribution"]).dt.days
    all_contributions["is_returning"] = all_contributions["days_since_last"] >= 90
    
    # vectorized first and last action matrices to prevent index errors
    all_contributions["first_ever_date"] = all_contributions.groupby(["repo_id", "username"])["contribution_time"].transform("min")
    all_contributions["last_ever_date"] = all_contributions.groupby(["repo_id", "username"])["contribution_time"].transform("max")
    
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date + "T23:59:59")
    
    bus_results = []
    trend_rows = []
    
    # print("\n--- DETAILED ECOSYSTEM COMMUNITY HEALTH PRINT OUT ---")
    
    for repo_id, repo_group in all_contributions.groupby("repo_id"):
        default_name = "Repository ID: " + str(repo_id)
        repo_name = repo_map.get(repo_id, default_name)
        
        # print(f"\n{'='*60}\nRepository: {repo_name}\nTimeline: {start_date} to {end_date}\n{'='*60}")
        
        # filter window slice for standard macro evaluation context
        window_contributions = repo_group[(repo_group["contribution_time"] >= start_dt) & 
                                          (repo_group["contribution_time"] <= end_dt)].copy()
        
        if not window_contributions.empty:
            active_names = window_contributions["username"].unique()
            returning_contributions = window_contributions[window_contributions["is_returning"] == True]
            returning_names = list(returning_contributions["username"].unique())
            
            # Contributor Absence Factor (Ecosystem Churn)
            churned_count = 0
            distinct_users = repo_group.drop_duplicates(subset=["username"])
            for _, row in distinct_users.iterrows():
                if row["last_ever_date"] < (end_dt - pd.Timedelta(days=90)):
                    churned_count += 1
            
            # Bus Factor calculations
            user_counts = window_contributions.groupby("username").size().reset_index(name="contribution_count")
            group_sorted = user_counts.sort_values(by="contribution_count", ascending=False)
            
            total_contributions = group_sorted["contribution_count"].sum()
            threshold = total_contributions * 0.50
            cumulative_contributions = 0
            bus_factor = 0
            bus_factor_names = []
            
            for _, row in group_sorted.iterrows():
                cumulative_contributions += row["contribution_count"]
                bus_factor += 1
                bus_factor_names.append(row["username"])
                if cumulative_contributions > threshold:
                    break
            
            # print(f"  Total Unique Active Contributors: {len(active_names)}")
            # print(f"  Total Actions Analyzed (Commits/PRs/Issues/Comments): {total_contributions}")
            # print(f"  Ecosystem Bus Factor Score: {bus_factor}")
            # print(f"  Key Core Maintainers ('Bus People'): {', '.join(bus_factor_names)}")
            # print(f"  Returning Contributors (90+ day absence): {len(returning_names)}")
            # print(f"  CHAOSS Contributor Absence Factor (Inactive/Churned Count): {churned_count}")
            
            bus_results.append({
                "Repository": repo_name,
                "Total Contributors": len(active_names),
                "Total Contributions": total_contributions,
                "Bus Factor (50%)": bus_factor,
                "Key People": ", ".join(bus_factor_names),
                "Returning Count": len(returning_names),
                "Absence Factor (Churn)": churned_count
            })
            
            # Monthly Rolling Contributor Trend Calculation
            window_contributions["month"] = window_contributions["contribution_time"].dt.strftime("%Y-%m")
            
            for month_name, month_group in window_contributions.groupby("month"):
                month_active_users = month_group.drop_duplicates(subset=["username"])
                
                new_count = 0
                ret_count = 0
                
                for _, user_row in month_active_users.iterrows():
                    if user_row["first_ever_date"].strftime("%Y-%m") == month_name:
                        new_count += 1
                    else:
                        ret_count += 1
                        
                trend_rows.append({
                    "repo_name": repo_name,
                    "month": month_name,
                    "new_contributors": new_count,
                    "returning_contributors": ret_count
                })
                
    return pd.DataFrame(bus_results), pd.DataFrame(trend_rows)

# !!!!!!!!!!!!!!!!
# GRAPH GENERATION
# !!!!!!!!!!!!!!!!

def plot_pr_velocity_and_efficiency(df_pr):
    """
    chart for RQ1 - note it's a dual-axis combo chart showcasing Velocity and Closure Ratio
    """
    fig, ax1 = plt.subplots(figsize=(10, 6))
    repos = df_pr['repository_name'].values
    x_pos = range(len(repos))
    bar_width = 0.4
    
    color_days = '#2b5c8f'
    
    # updated from 'avg_merge_days' to 'median_merge_days'
    bars = ax1.bar(x_pos, df_pr['median_merge_days'], width=bar_width, color=color_days, alpha=0.85, label='Median Days to Merge')
    
    ax1.set_xlabel('Library', labelpad=12, weight='bold')
    
    # updated label text to median
    ax1.set_ylabel('Median Velocity (Days to Merge Code)', color=color_days, weight='bold')
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(repos, weight='bold')
    ax1.tick_params(axis='y', labelcolor=color_days)
    ax1.grid(True, axis='y', alpha=0.5)
    
    for bar in bars:
        height = bar.get_height()
        ax1.annotate(f'{height:.1f} Days',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, color='#333333', weight='bold')

    ax2 = ax1.twinx()
    color_ratio = '#d95f02'
    ax2.plot(x_pos, df_pr['closure_ratio'], color=color_ratio, marker='o', linewidth=2.5, markersize=8, label='Closure Ratio')
    
    ax2.set_ylabel('Change Request Closure Ratio (Closed/Open)', color=color_ratio, weight='bold')
    ax2.tick_params(axis='y', labelcolor=color_ratio)
    ax2.set_ylim(0, max(df_pr['closure_ratio']) * 1.2 + 0.5)
    ax2.spines['right'].set_visible(True)
    
    for i, txt in enumerate(df_pr['closure_ratio'].values):
        ax2.annotate(f'{txt:.2f}x', (x_pos[i], df_pr['closure_ratio'].values[i]),
                    textcoords="offset points", xytext=(0,10), ha='center', color=color_ratio, weight='bold')

    # !!! CHANGED HERE: updated title text !!!
    plt.title('PR Process Median Velocity vs. Change Request Closure Ratio (RQ1)', pad=20, weight='bold', fontsize=15)
    fig.tight_layout()
    plt.savefig('pr_velocity_detailed.png', dpi=300)
    plt.close()

def plot_contributor_trends(df_dynamics):
    """
    Side-by-side trend line plots for each repo. 
    Dynamically switches between monthly and annual views depending on 
    the size of the timeline window, preventing X-axis clutter.
    """
    if df_dynamics.empty:
        return
        
    df_dynamics = df_dynamics.copy()
    unique_months = df_dynamics['month'].nunique()
    
    # DYNAMIC TIME RE-SAMPLING:
    # If the timeframe spans more than 2 years (24 months), aggregate into Years.
    # Otherwise, keep the original month-by-month breakdown.
    if unique_months > 24:
        df_dynamics['time_hub'] = df_dynamics['month'].apply(lambda x: x.split('-')[0])
        df_plot = df_dynamics.groupby(['repo_name', 'time_hub']).agg({
            'new_contributors': 'sum',
            'returning_contributors': 'sum'
        }).reset_index()
        x_label = "Timeline (Years)"
        title_suffix = "Annual Growth"
    else:
        df_plot = df_dynamics.copy()
        df_plot['time_hub'] = df_plot['month']
        x_label = "Timeline (Months)"
        title_suffix = "Monthly Growth"
        
    repos = df_plot['repo_name'].unique()
    fig, axes = plt.subplots(1, len(repos), figsize=(14, 5.5), sharey=True)
    
    color_ret = '#1f77b4'
    color_new = '#ff7f0e'
    
    if len(repos) == 1:
        axes = [axes]
        
    for i, repo in enumerate(repos):
        repo_data = df_plot[df_plot['repo_name'] == repo].sort_values(by='time_hub')
        ax = axes[i]
        
        ax.plot(repo_data['time_hub'], repo_data['returning_contributors'], 
                label='Returning Contributors', color=color_ret, linewidth=2.5, marker='o')
        ax.plot(repo_data['time_hub'], repo_data['new_contributors'], 
                label='New Contributors', color=color_new, linewidth=2, linestyle='--', marker='x')
        
        ax.set_title(f"{repo} {title_suffix}", fontsize=13, pad=12, weight='bold', color='#333333')
        ax.set_xlabel(x_label, labelpad=10)
        ax.grid(True, axis='y', alpha=0.4)
        
        ax.set_xticks(range(len(repo_data['time_hub'])))
        
        # If it's a short period, show all months. If it's a massive period, show all years.
        # But if it's somewhere in between (e.g., 3-5 years), skip labels so they never overlap.
        labels = repo_data['time_hub'].values
        if len(labels) > 15:
            # Only display every 2nd label if the axis starts to get crowded
            ax.set_xticklabels([label if idx % 2 == 0 else '' for idx, label in enumerate(labels)], rotation=45, ha='right')
        else:
            ax.set_xticklabels(labels, rotation=45, ha='right')
        
        if i == 0:
            ax.set_ylabel("Contributor Count", weight='bold')
            ax.legend(frameon=True, facecolor='#ffffff', edgecolor='none', loc='upper left')
            
    plt.tight_layout()
    plt.show()
    # plt.savefig('contributor_trends.png', dpi=300)
    # plt.close()

def plot_bus_factor_comparison(df_bus):
    """
    clean horizontal bar chart visualizing the new ecosystem bus factor for each repo, RQ2
    """
    fig, ax = plt.subplots(figsize=(8, 3.5))
    df_sorted = df_bus.sort_values(by='Bus Factor (50%)', ascending=True)
    
    bars = ax.barh(df_sorted['Repository'], df_sorted['Bus Factor (50%)'], 
                  color=['#aec7e8', '#2b5c8f'], height=0.55, edgecolor='none')
    
    ax.set_xlabel('Ecosystem Bus Factor Index (Top People Generating 50% of Total Operations)', labelpad=10, weight='bold')
    ax.set_title('Ecosystem Resilience & Structural Key-Man Risk (RQ2)', pad=20, weight='bold', fontsize=14)
    ax.set_xlim(0, max(df_bus['Bus Factor (50%)']) + 3)
    ax.grid(True, axis='x', alpha=0.4)
    
    for bar in bars:
        width = bar.get_width()
        ax.annotate(f' {int(width)} Key Contributors',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0), textcoords="offset points",
                    ha='left', va='center', fontsize=11, weight='bold', color='#333333')
                    
    ax.set_yticklabels(df_sorted['Repository'], weight='bold', fontsize=12, color='#222222')
    ax.spines['left'].set_visible(False)
    
    plt.tight_layout()
    plt.savefig('bus_factor_comparison.png', dpi=300)
    plt.close()

if __name__ == "__main__":
    start_date = get_dates('start date')
    end_date = get_dates('end date')
    # print("\nStarting metrics calculation:")
    
    # 1. PR Velocity RQ1
    # print("\n--- METRIC: PULL REQUEST VELOCITY & CLOSURE RATIOS (RQ1) ---")
    df_pr = analyze_pr_metrics_detailed(start_date, end_date)
    # print(df_pr.to_string(index=False))
    plot_pr_velocity_and_efficiency(df_pr)
    # print("'pr_velocity_detailed.png' saved")
    
    # 2. Advanced Ecosystem Analytics RQ2
    df_bus_summary, df_monthly_trends = analyze_ecosystem_community_dynamics(start_date, end_date)
    
    # print out summary frames and draw the updated charts
    # print(df_bus_summary.to_string(index=False))

    plot_bus_factor_comparison(df_bus_summary)
    # print("'bus_factor_comparison.png' saved")

    plot_contributor_trends(df_monthly_trends)
    # print("'contributor_trends.png' saved")
    
    # print("\nPhotos printed")