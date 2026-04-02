"""Combine cumulative statistics from GitHub clones and Zenodo downloads."""

import os
from datetime import datetime as dt
from glob import glob

import numpy as np
import pandas as pd
import yaml


def _spread_initial(series, full_index, spread_from):
    """Spread the first non-zero cumulative value evenly from *spread_from*.

    Parameters
    ----------
    series : pd.Series
        Raw cumulative series (indexed by date, may have gaps).
    full_index : pd.DatetimeIndex
        The complete date index to reindex onto.
    spread_from : pd.Timestamp
        Earliest date to include in the spread.

    Returns
    -------
    pd.Series
        Cumulative series on *full_index* with the initial value spread.
    """
    sorted_s = series.sort_index()

    # Find the first non-zero entry
    nonzero = sorted_s[sorted_s > 0]
    if nonzero.empty:
        return pd.Series(0.0, index=full_index)

    first_date = nonzero.index[0]
    first_val = nonzero.iloc[0]
    first_pos = sorted_s.index.get_loc(first_date)

    # Dates to spread across: from spread_from up to (and including) first_date
    dates_to_spread = full_index[
        (full_index >= spread_from) & (full_index <= first_date)
    ]
    n_days = len(dates_to_spread)

    result = pd.Series(0.0, index=full_index)
    if n_days > 0:
        base = first_val / n_days
        cumulative = np.arange(1, n_days + 1) * base
        # Ensure the last value is exact (avoid floating-point drift)
        cumulative[-1] = first_val
        result.loc[dates_to_spread] = cumulative

    # Carry the initial value forward to all dates after the spread period
    result.loc[full_index > first_date] = first_val

    # Add daily deltas AFTER the first non-zero entry (which the spread
    # already accounts for)
    for i in range(first_pos + 1, len(sorted_s)):
        date_i = sorted_s.index[i]
        delta = sorted_s.iloc[i] - sorted_s.iloc[i - 1]
        if delta != 0:
            result.loc[full_index >= date_i] += delta

    return result


# Per-repo overrides: if a repo was released / started tracking later than
# the global start date, spread its initial counts from this date instead.
REPO_RELEASE_DATES = {
    "metapsy-project/data-ptsd-mdmactr": pd.Timestamp("2026-02-23"),
}


def main(clone_folder, zenodo_folder, data_dir):
    """Combine cumulative statistics for all repositories and sources.

    GitHub clones and Zenodo downloads are merged into a single column per
    repository.  Initial cumulative snapshots are spread evenly so the graph
    doesn't show a sudden spike.  Subsequent daily deltas are added normally.

    Parameters
    ----------
    clone_folder : str
        Path to the directory containing GitHub clone cumulative CSVs.
    zenodo_folder : str
        Path to the directory containing Zenodo cumulative CSVs.
    data_dir : str
        Path to the _data directory for writing download_totals.yml.
    """
    github_dfs = {}
    zenodo_dfs = {}

    # Read GitHub clone cumulative files
    clone_files = sorted(
        glob(os.path.join(clone_folder, "metapsy-project_*_cum_clones.csv"))
    )
    for file_ in clone_files:
        repo_name = os.path.basename(file_).split("_cum_clones")[0]
        repo_name = repo_name.replace("_", "/", 1)
        df = pd.read_csv(file_, index_col="date")
        df.index = pd.to_datetime(df.index)
        df = df.rename({"clone_count": repo_name}, axis=1)
        df = df.loc[~df.index.duplicated(keep="first")]
        github_dfs[repo_name] = df

    # Read Zenodo cumulative files
    if os.path.isdir(zenodo_folder):
        zenodo_files = sorted(
            glob(os.path.join(zenodo_folder, "metapsy-project_*_cum_zenodo.csv"))
        )
        for file_ in zenodo_files:
            repo_name = os.path.basename(file_).split("_cum_zenodo")[0]
            repo_name = repo_name.replace("_", "/", 1)
            df = pd.read_csv(file_, index_col="date")
            df.index = pd.to_datetime(df.index)
            df = df.rename({"download_count": repo_name}, axis=1)
            df = df.loc[~df.index.duplicated(keep="first")]
            zenodo_dfs[repo_name] = df

    all_repos = sorted(set(list(github_dfs.keys()) + list(zenodo_dfs.keys())))
    if not all_repos:
        return

    # Build a combined date index from all sources, including any release
    # dates that may precede the earliest data point
    all_dates = set()
    for df in list(github_dfs.values()) + list(zenodo_dfs.values()):
        all_dates.update(df.index)
    for d in REPO_RELEASE_DATES.values():
        all_dates.add(d)
    full_index = pd.DatetimeIndex(sorted(all_dates))

    # Merge GitHub + Zenodo per repo
    merged = pd.DataFrame(index=full_index)
    for repo in all_repos:
        gh = github_dfs.get(repo)
        zen = zenodo_dfs.get(repo)

        # Default spread-from date: global start of tracking
        spread_from = REPO_RELEASE_DATES.get(repo, full_index[0])

        # GitHub cumulative series
        if gh is not None:
            gh_series = _spread_initial(gh[repo], full_index, spread_from)
        else:
            gh_series = pd.Series(0.0, index=full_index)

        # Zenodo cumulative series
        if zen is not None and len(zen) > 0:
            zen_series = _spread_initial(zen[repo], full_index, spread_from)
            merged[repo] = gh_series + zen_series
        else:
            merged[repo] = gh_series

    # Round to avoid floating-point display noise
    merged = merged.round(1)

    # Calculate overall cumulative count
    merged["Overall"] = merged[all_repos].sum(axis=1).round(1)

    # Write combined cumulative CSV
    overall_file = os.path.join(clone_folder, "all_repos_cumulative.csv")
    merged.to_csv(overall_file, index_label="date")

    # Generate download_totals.yml for Jekyll sidebar
    generate_totals_yaml(merged, all_repos, data_dir)


def generate_totals_yaml(df_cum, repos, data_dir):
    """Generate a YAML file with per-repo and overall download totals.

    Parameters
    ----------
    df_cum : pd.DataFrame
        The combined cumulative DataFrame.
    repos : list
        List of repository column names.
    data_dir : str
        Path to the _data directory.
    """
    last_row = df_cum.iloc[-1]
    today = df_cum.index[-1].strftime("%Y-%m-%d")

    totals = {}
    for repo in repos:
        totals[repo] = {"total": int(last_row[repo])}

    totals["overall"] = int(last_row["Overall"])
    totals["last_updated"] = today

    totals_file = os.path.join(data_dir, "download_totals.yml")
    with open(totals_file, "w") as f:
        yaml.dump(totals, f, default_flow_style=False, sort_keys=False)


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    clone_dir = os.path.abspath(
        os.path.join(script_dir, "../../_data/clone-tracking/cumulative")
    )
    zenodo_dir = os.path.abspath(
        os.path.join(script_dir, "../../_data/zenodo-tracking/cumulative")
    )
    data_dir = os.path.abspath(os.path.join(script_dir, "../../_data"))
    main(clone_dir, zenodo_dir, data_dir)
