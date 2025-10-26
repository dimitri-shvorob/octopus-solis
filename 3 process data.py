import json
from pathlib import Path

import polars as pl

PATH = Path(r"C:\Users\dimit\Documents\GitHub\octopus-solis")

# octopus tariffs - adjusted for VAT
with Path.open(PATH / "octopus_tariffs.json") as f:
    tariffs = json.load(f)

dts = []
for key, value in tariffs.items():
    dt = ( 
        pl.from_dicts(value).with_columns(
        type=pl.lit(key),
        effective_from=pl.col("effective_from").str.to_date(),
        effective_to=pl.col("effective_to").str.to_date(),
    )
    .with_columns(charge_per_kwh = pl.when(pl.col.type == "electric_export").then(pl.col.charge_per_kwh).otherwise(1.05*pl.col.charge_per_kwh))
    .with_columns(standing_charge = 1.05*pl.col.standing_charge)
    )    
    dts.append(dt)
dt = pl.concat(dts, how="diagonal").sort("type", "effective_from")

# solis daily generation
ds = pl.read_csv(PATH / "data solis.csv", try_parse_dates=True).drop_nulls(
    subset="value_kwh_electric_generation"
)

# octopus usage
df1 = (
    pl.read_parquet(PATH / "data octopus" / "*.parquet")
    .with_columns(date=pl.col("start_time").dt.date())
    .drop("start_time")
    .group_by("type", "date")
    .sum()
)

# convert values to values kwh
GAS_KWH_PER_UNIT = 11.13541
df1 = df1.with_columns(value_kwh = pl.when(pl.col.type == "gas").then(pl.col.value*pl.lit(GAS_KWH_PER_UNIT)).otherwise(pl.col.value)).drop("value")

# date/type spine
df2 = (
    pl.DataFrame(data=["electric_import", "electric_export", "gas"], schema=["type"])
    .join(pl.DataFrame(data=pl.date_range(start=df1["date"].min(), end=df1["date"].max(), eager=True), schema=["date"]), how="cross")
    .join(df1, on=["date", "type"], how="left")
    .sort("type", "date")
)
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
        value_gbp=pl.col.standing_charge + pl.col.value_kwh * pl.col.charge_per_kwh
    )
)

# pivot and link up solis data
df4 = (
    df3.pivot(on="type", index="date")
    .join(ds, on="date", how="left", coalesce=True)
    .with_columns(
        value_kwh_electric_generation=pl.when(
            pl.col.value_kwh_electric_generation.is_null()
            & ~pl.col.value_kwh_electric_export.is_null()
        )
        .then(pl.col.value_kwh_electric_export)
        .otherwise(pl.col.value_kwh_electric_generation)
    )
    .fill_nan(0)
    .fill_null(0)
    .with_columns(
        value_kwh_electric_generation_consumed=pl.col.value_kwh_electric_generation
        - pl.col.value_kwh_electric_export
    )
    .with_columns(
        value_gbp_electric_import_avoided=pl.col.charge_per_kwh_electric_import
        * pl.col.value_kwh_electric_generation_consumed
    )
    .with_columns(
        value_gbp_electric_savings=pl.col.value_gbp_electric_import_avoided
        + pl.col.value_gbp_electric_export
    )
    .with_columns(
        value_gbp_electric_savings_battery_max=(
            pl.col.charge_per_kwh_electric_import
            - pl.col.charge_per_kwh_electric_export
        )
        * pl.when(
            pl.col.value_kwh_electric_import < pl.col.value_kwh_electric_generation
        )
        .then(pl.col.value_kwh_electric_import)
        .otherwise(pl.col.value_kwh_electric_generation)
    )
    .with_columns(
        month=pl.col("date").dt.truncate("1mo"),
        month_short=pl.col("date").dt.month(),
        year=pl.col("date").dt.year(),
    )
    .sort("date")
    .with_columns(
        cum_value_gbp_electric_export=pl.col.value_gbp_electric_export.cum_sum(),
        cum_value_gbp_electric_import_avoided=pl.col.value_gbp_electric_import_avoided.cum_sum(),
        cum_value_gbp_electric_savings=pl.col.value_gbp_electric_savings.cum_sum(),
        cum_value_gbp_electric_savings_battery_max=pl.col.value_gbp_electric_savings_battery_max.cum_sum(),
    )
)
df4.write_csv(PATH / "OUTPUT data octopus and solis wide.csv")
df4.write_parquet(PATH / "OUTPUT data octopus and solis wide.parquet")
