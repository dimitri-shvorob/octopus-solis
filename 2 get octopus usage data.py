import datetime
import json
from pathlib import Path

import polars as pl
import requests

PATH = Path(r"C:\Users\dimit\Documents\GitHub\octopus-solis")

with Path.open(PATH / "secrets.json") as f:
    secrets = json.load(f)

dates = pl.date_range(
    start=datetime.date(2025, 7, 17), end=datetime.date(2025, 7, 18), eager=True
)

for date in dates:
    date_str = date.isoformat()
    print(date)
    params = {
        "period_from": f"{date_str}:00:00:00Z",
        "period_to": f"{date_str}T23:30:00Z",
    }
    dfs = []
    for label, url in secrets["api_endpoints"].items():
        response = requests.get(
            url=url, auth=(secrets["api_key"], ""), params=params, timeout=10
        )
        d = response.json()["results"]
        if len(d) > 0:
            df = pl.DataFrame(d).with_columns(type=pl.lit(label))
            dfs.append(df)
    if len(dfs) > 0:
        df = (
            pl.concat(dfs, how="diagonal")
            .with_columns(
                start_time_utc=pl.col("interval_start").str.to_datetime(
                    "%Y-%m-%dT%H:%M:%S%#z"
                )
            )
            .with_columns(
                start_time=pl.col("start_time_utc").dt.convert_time_zone(
                    "Europe/London"
                )
            )
            .select("start_time", "type", "consumption")
            .rename({"consumption": "value_kwh"})
        )
        df.write_parquet(PATH / "data octopus" / f"{date.isoformat()}.parquet")
