from pathlib import Path

import polars as pl

PATH = Path(r"C:\Users\dimit\Documents\GitHub\octopus-solis")

df = pl.read_csv(PATH / "scripts" / "data octopus old.csv").with_columns(
    date=pl.col("start_time").str.slice(0, 10)
)

pp = df.partition_by("date", as_dict=True)

for key, p in pp.items():
    print(key[0])
    p = p.drop("date").with_columns(
        start_time=pl.col("start_time").str.to_datetime(
            "%d/%m/%Y %H:%M", time_zone="Europe/London"
        )
    )
    date_str = p["start_time"].min().isoformat()[:10]
    p.write_parquet(PATH / "data octopus" / f"{date_str}.parquet")
