"""Fetch cumulative download statistics from Zenodo for each dataset."""

import json
import os
import time
import urllib.request
from datetime import datetime as dt

import pandas as pd


def main(repo, concept_recid):
    """Fetch cumulative download count from Zenodo and append to a CSV.

    Parameters
    ----------
    repo : str
        The name of the repository in the format "owner/repo".
    concept_recid : str
        The Zenodo concept record ID (stable across all versions).
    """
    print(f"Fetching Zenodo download statistics for {repo} (concept recid: {concept_recid})...")

    stats = fetch_zenodo_stats(concept_recid)
    if stats is None:
        print(f"  Skipping {repo} due to Zenodo API error.")
        return

    downloads = stats.get("downloads", 0)
    today = dt.now().strftime("%Y-%m-%d")
    print(f"  Cumulative downloads (all versions): {downloads}")

    owner_name, repo_name = repo.split("/")

    script_dir = os.path.dirname(__file__)
    cum_dir = os.path.abspath(
        os.path.join(script_dir, "../../_data/zenodo-tracking/cumulative")
    )
    os.makedirs(cum_dir, exist_ok=True)

    cum_file = os.path.join(cum_dir, f"{owner_name}_{repo_name}_cum_zenodo.csv")

    if os.path.isfile(cum_file):
        df = pd.read_csv(cum_file, index_col="date")
        df.index = pd.to_datetime(df.index)
    else:
        df = pd.DataFrame(columns=["download_count"])
        df.index.name = "date"

    today_dt = pd.to_datetime(today)
    if today_dt in df.index:
        # Update today's entry if it already exists
        df.loc[today_dt, "download_count"] = downloads
    else:
        new_row = pd.DataFrame(
            {"download_count": [downloads]},
            index=pd.DatetimeIndex(data=[today_dt], name="date"),
        )
        df = pd.concat([df, new_row])

    df = df.sort_index()
    df.to_csv(cum_file, index_label="date")


def fetch_zenodo_stats(concept_recid, retries=1):
    """Fetch download statistics from the Zenodo API.

    Parameters
    ----------
    concept_recid : str
        The Zenodo concept record ID.
    retries : int
        Number of retries on failure.

    Returns
    -------
    dict or None
        The stats dict from the Zenodo API response, or None on failure.
    """
    url = f"https://zenodo.org/api/records/{concept_recid}"

    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data.get("stats", {})
        except Exception as e:
            print(f"  Zenodo API error (attempt {attempt + 1}): {e}")
            if attempt < retries:
                time.sleep(5)

    return None


if __name__ == "__main__":
    ZENODO_DATASETS = [
        ("metapsy-project/data-depression-psiloctr", "15714852"),
        ("metapsy-project/data-ptsd-mdmactr", "18740439"),
    ]
    for repo, concept_recid in ZENODO_DATASETS:
        main(repo, concept_recid)
