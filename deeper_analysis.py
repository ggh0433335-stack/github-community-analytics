import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def deep_analysis_graphs():
    connection = sqlite3.connect("project_data.db")
    cursor = connection.cursor()

    def get_date(prompt):
        while True:
            search_year = int(input(f'What {prompt} do you want to check? '))
            search_quarter = input('What quarter do you want to check? ').upper()
            try:
                if search_quarter not in ('Q1', 'Q2', 'Q3', 'Q4'):
                    raise ValueError
                
                quarter_months = {'Q1': 1, 'Q2': 4, 'Q3': 7, 'Q4': 10}
                if prompt == 'end year':
                    month = quarter_months[search_quarter] + 3
                else:
                    month = quarter_months[search_quarter]


                return f"{search_year}-{month:02d}-01"  
            
            except (ValueError, AttributeError):
                print("  Invalid format. Please enter as 'YYYY' and 'Q#' (e.g. 2016 Q3)\n")

    start_search = get_date('start year')
    end_search = get_date('end year')
    # CONCENTRATION QUERIES   

    # number of total reviews per quarter
    total_reviews  = f"""
        SELECT 
            r.name,
            strftime('%Y', prr.submitted_at) AS year,

            CASE
                WHEN CAST(strftime('%m', prr.submitted_at) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
                WHEN CAST(strftime('%m', prr.submitted_at) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
                WHEN CAST(strftime('%m', prr.submitted_at) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
                ELSE 'Q4'
            END AS quarter,

            COUNT(DISTINCT prr.id) AS reviews
        
        FROM pr_reviews prr
        JOIN pull_requests pr ON prr.pr_id = pr.id
        JOIN repositories r ON pr.repo_id = r.id
        WHERE prr.submitted_at >= '{start_search}'
            AND prr.submitted_at < '{end_search}'
        GROUP BY r.name, year, quarter;
    """

    cursor.execute(total_reviews)
    total_pr_reviews: list = cursor.fetchall()
    # print(total_pr_reviews)
    # print('total_pr_reviews:', len(total_pr_reviews))

    # number of reviews corresponding to most active contributor quarterly

    top_reviewers = f"""
        SELECT repo_name, reviewer_id, year, quarter, review_count
        FROM (
            SELECT *,
                ROW_NUMBER() OVER (
                    PARTITION BY repo_name, year, quarter
                    ORDER BY review_count DESC
                ) AS ranking
            FROM (
                SELECT  
                    r.name AS repo_name, 
                    prr.reviewer_id,
                    strftime('%Y', prr.submitted_at) AS year,
                    CASE
                        WHEN CAST(strftime('%m', prr.submitted_at) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
                        WHEN CAST(strftime('%m', prr.submitted_at) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
                        WHEN CAST(strftime('%m', prr.submitted_at) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
                        ELSE 'Q4'
                    END AS quarter,
                    COUNT(*) AS review_count
                FROM pr_reviews prr
                JOIN pull_requests pr ON prr.pr_id = pr.id
                JOIN repositories r ON pr.repo_id = r.id
                WHERE pr.merged_at IS NOT NULL
                    AND prr.submitted_at >= '{start_search}'
                    AND prr.submitted_at < '{end_search}'
                GROUP BY r.name, year, quarter, prr.reviewer_id
            ) aggregated
        ) ranked
        WHERE ranking = 1 
        ORDER BY repo_name, year, quarter;
    """

    cursor.execute(top_reviewers)
    best_reviewer_count: list = cursor.fetchall()     #repo, reviewer id, year, quarter, num of reviews
    # print(best_reviewer_count)
    # print('best_reviewer_count:', len(best_reviewer_count))


    # CALCULATIONS FOR CONCENTRATION     
    # number of most active contributor’s reviews  / total reviews * 100 (per quarter)


    concentration_pandas: dict[str : list] = {'Concentration' : [], 'year' : [], 'Q#' : [], 'ID' : []}
    concentration_scikit: dict[str : list] = {'Concentration' : [], 'year' : [], 'Q#' : [], 'ID' : []} # concentration, year, quarter, contributor id

    for review in range(len(total_pr_reviews)):
        top_collaborator: tuple = best_reviewer_count[review]
        t_review: tuple = total_pr_reviews[review]

        if top_collaborator[0] == 'pandas':
            concentration_pandas['Concentration'].append(round((top_collaborator[4] / t_review[3]) * 100))
            concentration_pandas['year'].append(top_collaborator[2])
            concentration_pandas['Q#'].append(top_collaborator[3])
            concentration_pandas['ID'].append(top_collaborator[1])
        else:
            concentration_scikit['Concentration'].append(round((top_collaborator[4] / t_review[3]) * 100))
            concentration_scikit['year'].append(top_collaborator[2])
            concentration_scikit['Q#'].append(top_collaborator[3])
            concentration_scikit['ID'].append(top_collaborator[1])

    # COVERAGE QUERIES

    # total merged PRs per quarter
    merged_pr_quarter = f"""
        SELECT 
            r.name,
            strftime('%Y', pr.merged_at) AS year,

            CASE
                WHEN CAST(strftime('%m', pr.merged_at) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
                WHEN CAST(strftime('%m', pr.merged_at) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
                WHEN CAST(strftime('%m', pr.merged_at) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
                ELSE 'Q4'
            END AS quarter,

            COUNT(DISTINCT pr.id) AS merged_pr
        
        FROM pull_requests pr
        JOIN repositories r ON pr.repo_id = r.id    
        WHERE pr.merged_at IS NOT NULL
            AND pr.merged_at >= '{start_search}'
            AND pr.merged_at < '{end_search}'
        GROUP BY r.name, year, quarter;
    """

    cursor.execute(merged_pr_quarter)
    total_merged_PRs: list = cursor.fetchall()
    # print(total_merged_PRs)
    # print('total_merged_PRs:', len(total_merged_PRs))

    # merged PRs without reviews per quarter
    noreview_pr_quarter = f"""
        SELECT 
            r.name,
            strftime('%Y', pr.merged_at) AS year,

            CASE
                WHEN CAST(strftime('%m', pr.merged_at) AS INTEGER) BETWEEN 1 AND 3 THEN 'Q1'
                WHEN CAST(strftime('%m', pr.merged_at) AS INTEGER) BETWEEN 4 AND 6 THEN 'Q2'
                WHEN CAST(strftime('%m', pr.merged_at) AS INTEGER) BETWEEN 7 AND 9 THEN 'Q3'
                ELSE 'Q4'
            END AS quarter,

            COUNT(DISTINCT CASE WHEN prr.pr_id IS NULL THEN pr.id END) AS no_review_pr

        FROM pull_requests pr
        LEFT JOIN pr_reviews prr ON pr.id = prr.pr_id
        JOIN repositories r ON pr.repo_id = r.id
        WHERE pr.merged_at IS NOT NULL
            AND pr.merged_at >= '{start_search}'
            AND pr.merged_at < '{end_search}'
        GROUP BY r.name, year, quarter;
    """

    cursor.execute(noreview_pr_quarter)
    total_merged_PRs_without_reviews: list = cursor.fetchall()
    # print(total_merged_PRs_without_reviews)
    # print('total_merged_PRs_without_reviews:',len(total_merged_PRs_without_reviews))

    get_logins = """
        SELECT id, login
        FROM contributors;
    """
    cursor.execute(get_logins)
    logins = dict(cursor.fetchall())

    # COVERAGE CALCULATIONS

    # number of merged PRs without review / total merged PRs * 100 (per quarter)

    coverage_pandas: dict[str : list] = {'Coverage' : [], 'year' : [], 'Q#' : []}
    coverage_scikit: dict[str : list] = {'Coverage' : [], 'year' : [], 'Q#' : []}    # coverage, year, quarter

    for pr in range(len(total_merged_PRs)):
        pr_noreview: tuple = total_merged_PRs_without_reviews[pr]
        total_pr: tuple = total_merged_PRs[pr]

        if pr_noreview[0] == "pandas":
            coverage_pandas['Coverage'].append(round((1 - (pr_noreview[3] / total_pr[3])) * 100))
            coverage_pandas['year'].append(pr_noreview[1])
            coverage_pandas['Q#'].append(pr_noreview[2])
        else:
            coverage_scikit['Coverage'].append(round((1 - (pr_noreview[3] / total_pr[3])) * 100))
            coverage_scikit['year'].append(pr_noreview[1])
            coverage_scikit['Q#'].append(pr_noreview[2])

    X_concentration_pandas = pd.DataFrame(concentration_pandas)
    X_concentration_pandas["period"] = X_concentration_pandas["year"] + "-" + X_concentration_pandas["Q#"]

    Y_coverage_pandas = pd.DataFrame(coverage_pandas)
    Y_coverage_pandas["period"] = Y_coverage_pandas["year"] + "-" + Y_coverage_pandas["Q#"]

    # separataion 

    X_concentration_scikit = pd.DataFrame(concentration_scikit)
    X_concentration_scikit["period"] = X_concentration_scikit["year"] + "-" + X_concentration_scikit["Q#"]

    Y_coverage_scikit = pd.DataFrame(coverage_scikit)
    Y_coverage_scikit["period"] = Y_coverage_scikit["year"] + "-" + Y_coverage_scikit["Q#"]

    # concentration plot
    plt.figure(figsize=(14, 7))
    plt.plot(X_concentration_pandas["period"], X_concentration_pandas["Concentration"], color="steelblue", alpha=0.25, linewidth=1, zorder=1)
    plt.plot(X_concentration_scikit["period"], X_concentration_scikit["Concentration"], color="tomato", alpha=0.25, linewidth=1, zorder=1)

    # scatter plot 
    for df, color, label in [(X_concentration_pandas, "steelblue", "Pandas"), (X_concentration_scikit, "tomato", "Scikit")]:
        plt.scatter(df["period"], df["Concentration"], color=color, label=label, zorder=2, alpha=0.9, s=60)

    # annotate top contributor change per quarter
    for df, va, color in [(X_concentration_pandas, "bottom", "steelblue"), (X_concentration_scikit, "top", "tomato")]:
        prev = None
        for _, row in df.iterrows():
            name = logins[int(row["ID"])]
            if name != prev:
                plt.annotate(name, xy=(row["period"], row["Concentration"]), xytext=(4, 8), textcoords="offset points", fontsize=7.5, fontweight='bold', color=color, alpha=1,va=va, zorder=3)
                prev = name


    plt.title("Review Concentration Over Time")
    plt.xlabel("Quarter")
    plt.ylabel("Concentration (%)")
    plt.xticks(rotation=45, ha="right", fontsize=8)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # coverage plot
    plt.figure(figsize=(12, 5))
    plt.plot(Y_coverage_pandas["period"], Y_coverage_pandas["Coverage"], label="Pandas")
    plt.plot(Y_coverage_scikit["period"], Y_coverage_scikit["Coverage"], label="Scikit")
    plt.title("Review Coverage Over Time")
    plt.xlabel("Quarter")
    plt.ylabel("Coverage (%)")
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()

    # concentration calculation 
    pandas_correlation = round(X_concentration_pandas["Concentration"].corr(Y_coverage_pandas["Coverage"],method='spearman'), 2)
    scikit_correlation = round(X_concentration_scikit["Concentration"].corr(Y_coverage_scikit["Coverage"],method='spearman'), 2)

    # CORRELATION SCATTER PLOT

    # merge concentration and coverage on period for each project
    merged_pandas = X_concentration_pandas.merge(Y_coverage_pandas, on="period", suffixes=("_conc", "_cov"))
    merged_scikit = X_concentration_scikit.merge(Y_coverage_scikit, on="period", suffixes=("_conc", "_cov"))

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, merged, name, color in zip(axes,[merged_pandas, merged_scikit],["Pandas", "Scikit-learn"],["#185FA5","#D85A30"]):
        x = merged["Concentration"]
        y = merged["Coverage"]

        ax.scatter(x, y, color=color, alpha=0.6, s=60, zorder=3)

        # trend line
        m, b = np.polyfit(x, y, 1)
        x_line = np.linspace(x.min(), x.max(), 100)
        ax.plot(x_line, m * x_line + b, color=color, linewidth=1.5, linestyle="--", alpha=0.8)

        # label each point with its period
        for _, row in merged.iterrows():
            if int(row["period"][:4]) >= 2020:
                ax.annotate(row["period"], (row["Concentration"], row["Coverage"]),fontsize=7, ha="left", va="bottom", xytext=(4, 4), textcoords="offset points")
            
        # add danger zone shading 

        ax.axhspan(0, 80, alpha=0.07, color=color, label="Risk zone (<80% coverage)")
        ax.legend(fontsize=8)
        ax.set_ylim(0, 105)
        ax.axhline(y=80, color='gray', linewidth=0.8, linestyle=':', alpha=0.6) 

        r = x.corr(y, method="spearman")
        ax.set_title(f"{name}  (Spearman r = {r:.2f})")
        ax.set_xlabel("Reviewer concentration (Top contributor %)")
        ax.set_ylabel("Review coverage (merged PRs reviewed %)")
        ax.grid(True, linewidth=0.4, alpha=0.5)

    plt.suptitle("Reviewer Concentration vs Review Coverage", fontsize=13, fontweight="500")
    plt.tight_layout()
    plt.show()
    return None

if __name__ == "__main__":
    deep_analysis_graphs()