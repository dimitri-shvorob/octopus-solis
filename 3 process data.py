import json
from pathlib import Path

import polars as pl

PATH = Path(r"C:\Users\dimit\Documents\GitHub\octopus-solis")

# octopus tariffs
with Path.open(PATH / "octopus_tariffs.json") as f:
    tariffs = json.load(f)

dts = []
for key, value in tariffs.items():
    dt = pl.from_dicts(value).with_columns(
        type=pl.lit(key),
        effective_from=pl.col("effective_from").str.to_date(),
        effective_to=pl.col("effective_to").str.to_date(),
    )
    dts.append(dt)
dt = pl.concat(dts, how="diagonal").sort("effective_from")

# solis daily generation
ds = pl.read_csv(PATH / "data solis.csv", try_parse_dates=True).drop_nulls(
    subset="value_kwh_electric_generation"
)

# octopus usage
df1 = (
    pl.read_parquet(PATH / "data octopus" / "*.parquet")
    .with_columns(date=pl.col("start_time").dt.date())
    .drop("start_time")
    .group_by("date", "type")
    .sum()
)

# date/type spine
dg1 = pl.DataFrame(
    data=pl.date_range(start=df1["date"].min(), end=df1["date"].max(), eager=True),
    schema=["date"],
)
dg2 = pl.DataFrame(data=["electric_import", "electric_export", "gas"], schema=["type"])
df2 = dg1.join(dg2, how="cross").join(df1, on=["date", "type"], how="left")

# link up date spine, octopus usage and tariffs
# fill electric export with zeroes
df3 = (
    df2.join_asof(
        dt, by="type", left_on="date", right_on="effective_from", strategy="backward"
    )
    .drop("effective_from", "effective_to")
    .with_columns(
        value_kwh=pl.when(
            (pl.col.type == "electric_export") & pl.col.value_kwh.is_null()
        )
        .then(pl.lit(0))
        .otherwise(pl.col.value_kwh)
    )
    .with_columns(
        value_gbp=(pl.col.standing_charge + pl.col.value_kwh * pl.col.charge_per_kwh)
        / 100
    )
)

# check for gaps - do get one!
dx = df3.filter(pl.col.value_kwh.is_null())
assert len(dx) == 0  # noqa: S101

df3.write_parquet(PATH / "OUTPUT data octopus tall.parquet")

# pivot and link up solis data
df4 = (
    df3.pivot(on="type", index="date")
    .join(ds, on="date", how="left", coalesce=True)
    .fill_nan(0)
    .fill_null(0)
    .with_columns(
        value_kwh_electric_generation_consumed=pl.col.value_kwh_electric_generation
        - pl.col.value_kwh_electric_export
    )
    .with_columns(
        value_gbp_electric_import_avoided=(
            pl.col.charge_per_kwh_electric_import
            + pl.col.charge_per_kwh_electric_export
        )
        * pl.col.value_kwh_electric_generation_consumed
    )
    .with_columns(
        value_gbp_electric_savings=pl.col.value_gbp_electric_import_avoided
        + pl.col.value_gbp_electric_export
    )
    .with_columns(
        month=pl.col("date").dt.truncate("1mo"),
        month_short=pl.col("date").dt.month(),
        year=pl.col("date").dt.year(),
    )
    .sort("date")
    .with_columns(
        cum_value_gbp_electric_savings=pl.col.value_gbp_electric_savings.cum_sum()
    )
)

df4.write_parquet(PATH / "OUTPUT data octopus and solis wide.parquet")
