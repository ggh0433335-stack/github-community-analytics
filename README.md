# github-community-analytics

## Description

This project analyses the open-source health and long-term sustainability of the **pandas** and **scikit-learn** GitHub projects, evaluated using [CHAOSS community metrics](https://chaoss.community/kbtopic/all-metrics-models/). The analysis covers two research questions:

- **RQ1** - PR velocity and change request closure ratio
- **RQ2** - Ecosystem bus factor, contributor churn, review concentration, and review coverage

The final goal is to produce a data-driven investment recommendation for the client *P-Value Partners*.

## Visuals

The project produces the following outputs depending on which script is run:

- `pr_velocity_detailed.png` - bar + line chart of median PR merge time vs. closure ratio (RQ1)
- `bus_factor_comparison.png` - horizontal bar chart of bus factor per repository (RQ2)
- Contributor trend charts (new vs. returning contributors, displayed interactively)
- Review concentration and coverage charts over time with a Spearman correlation scatter plot
- `interactive_analysis_dashboard.html` - a fully self-contained interactive Plotly dashboard combining all of the above

## Installation

### Requirements

- **Python 3.10 or higher**
- The following third-party packages:

| Package | Version | Purpose |
|---|---|---|
| `pandas` | latest | Data manipulation in all analysis scripts |
| `matplotlib` | latest | Static charts (`descriptive_analysis.py`, `deeper_analysis.py`) |
| `numpy` | latest | Numerical operations and trend-line fitting (`deeper_analysis.py`) |
| `plotly` | latest | Interactive HTML dashboard (`interactive_analysis_dashboard.py`) |

All other imports (`sqlite3`, `json`, `argparse`, `re`, `webbrowser`, `pathlib`, `calendar`) are part of the Python standard library and need no installation.

### Setup steps

**1. Clone the repository**

```bash
git clone https://gitlab.tue.nl/k.sritharan/fdc_g15.git
cd fdc_g15
```

**2. Install dependencies**

```bash
pip install pandas matplotlib numpy plotly
```

## Usage

The scripts must be run **in order** the first time.

### Step 1 - Load data

```bash
python data_load.py
```

Reads `big_github_data.json` and populates `project_data.db` with the full relational schema (contributors, repositories, commits, pull requests, issues, labels, comments, reviews).

### Step 2 - Clean data

```bash
python data_cleaning.py
```

Removes bot accounts, incomplete records, and orphaned foreign-key references from all tables. Modifies `project_data.db` in place.

### Step 3 - Interactive demonstrations

Choose **one** of the following options:

#### Option A - Full interactive dashboard

```bash
python interactive_analysis_dashboard.py
```

Generates `interactive_analysis_dashboard.html` combining all metrics in a single interactive Plotly dashboard. Open in any modern browser by executing the html file (no server required).

Optional flags:

| Flag | Description |
|---|---|
| `--start 2016Q1` | Set start quarter without a prompt |
| `--end 2025Q4` | Set end quarter without a prompt |
| `--prompt` | Interactively prompt for quarters instead |
| `--db path/to/file.db` | Use a different SQLite database |
| `--output report.html` | Save under a different filename |
| `--self-contained` | Embed Plotly JS (no internet needed to view) |
| `--open` | Open the dashboard in your browser after generation |

```bash
python interactive_analysis_dashboard.py --start 2016Q1 --end 2025Q4 --open
```

#### Option B - Terminal demo

```bash
python Demo.py
```

Runs the deeper analysis graphs and the contributor trend plot directly in the terminal. No HTML file is generated. Prompts are the same as the individual scripts above.

## Extras

The projects final executable files are the ones outside the milestone **#** files, however they hold the rest of the code that was used to make our initial explorations, plots and and data aquisition. No previous handeling is needed for them just execute the file and they will print the output on the terminal or generate their respetive graphs. 

Outside of that all files from previous milestones currently run on the project_data.db, so it analyses more years, thus it might not be a direct reflection of what we saw during our first encounters with the smaller database containing only 2025 data. 

## Authors and acknowledgment

Gabriel Gomez Hernandez, Austėja Budzevičiūtė, Karrthic Sritharan, Zhivko Zhechev, Selen Acar, Michael Ehab Fawaz Haddadin

## Project status

Project completed. No further development is planned.