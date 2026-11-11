from deeper_analysis import deep_analysis_graphs
from descriptive_analysis import plot_contributor_trends, analyze_ecosystem_community_dynamics, get_dates

deep_analysis_graphs()
plot_contributor_trends(analyze_ecosystem_community_dynamics(get_dates('start date'), get_dates('end date'))[1])