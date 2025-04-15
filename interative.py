#%%

import polars as pl
from gearcalc import rear_teeth_col, gear_calculations, hub_ratio_col, gear_inches_col, metre_development_col, gain_ratio_col

pl.DataFrame.transform = lambda df, f, *args, **kwargs: f(df, *args, **kwargs)
pl.LazyFrame.transform = lambda df, f, *args, **kwargs: f(df, *args, **kwargs)

etrto_diameter_mm=349
tire_width_mm=35
front_teeth=50
rear_teeth_list=[11, 13, 15, 18]
hub_ratio_percent_list=[64, 100, 157]
crank_length_mm=170

#%%

rear_teeth_df = pl.DataFrame(range(11, 24 + 1), schema=["t1"]).lazy()
front_teeth_df = pl.DataFrame(range(44, 54 + 1, 2), schema=["front_teeth"]).lazy()
max_jump = 5

combinations = (
    rear_teeth_df
    .join_where(rear_teeth_df.select(t2=pl.col("t1")), pl.col("t2") > pl.col("t1"), pl.col("t2") - pl.col("t1") < max_jump)
    .join_where(rear_teeth_df.select(t3=pl.col("t1")), pl.col("t3") > pl.col("t2"), pl.col("t3") - pl.col("t2") < max_jump)
    .join_where(rear_teeth_df.select(t4=pl.col("t1")), pl.col("t4") > pl.col("t3"), pl.col("t4") - pl.col("t3") < max_jump)
    .join(front_teeth_df, how="cross")
    .with_columns(
        pl.concat_list(pl.selectors.starts_with("t").alias("rear_teeths"))
    )
    .unpivot(
        on=pl.selectors.starts_with("t"),
        index=["front_teeth", "rear_teeths"],
        value_name=rear_teeth_col,
    )
)

combinations.collect()

#%%
def polars_gears_dataframe(rear_teeth_list, rear_teeth_col, etrto_diameter_mm, tire_width_mm, front_teeth, crank_length_mm, hub_ratio=1.0):

    df = (
        pl.DataFrame(rear_teeth_list, schema=[rear_teeth_col]).lazy()
        .with_columns(
            etrto_diameter_mm=etrto_diameter_mm,
            tire_width_mm=tire_width_mm,
            front_teeth=front_teeth,
            crank_length_mm=crank_length_mm,
            hub_ratio=hub_ratio,
        )
    )

    return df


def polars_gear_calculations(df):
    calculations_cols = gear_calculations(
        etrto_diameter_mm=pl.col("etrto_diameter_mm"),
        crank_length_mm=pl.col("crank_length_mm"),
        front_teeth=pl.col("front_teeth"),
        hub_ratio=pl.col("hub_ratio"),
        rear_teeth=pl.col(rear_teeth_col),
        tire_width_mm=pl.col("tire_width_mm"),
    )

    df = (
        df
        .with_columns(**calculations_cols)
    )

    return df


def polars_apply_hub_rations(df, hub_ratios):
    return (
        df
        .drop("hub_ratio")
        .join(pl.DataFrame(hub_ratios, schema=["hub_ratio"]).select(pl.col("hub_ratio") / 100).lazy(), how="cross")
        .with_columns(
            pl.col(c) * pl.col("hub_ratio") for c in [gear_inches_col, metre_development_col, gain_ratio_col, hub_ratio_col]
        )
        .drop("hub_ratio")
    )

def calculate_overlap(df: pl.LazyFrame, index=["front_teeth"]):
    return (
        df
        .group_by(hub_ratio_col, *index)
        .agg(
            pl.min(metre_development_col).alias("min"),
            pl.max(metre_development_col).alias("max"), 
        )
        .with_columns(pl.col("max").shift(1).over(index, order_by=hub_ratio_col).alias("prev_max"))
        .with_columns(overlap = pl.col("prev_max") - pl.col("min"))
        # .with_columns(overlap = pl.max_horizontal(pl.col("overlap"), pl.lit(0)))

    )

df = polars_gears_dataframe(
    rear_teeth_list,
    rear_teeth_col,
    etrto_diameter_mm,
    tire_width_mm,
    front_teeth,
    crank_length_mm
)
df = polars_gear_calculations(df)
df = polars_apply_hub_rations(df, hub_ratio_percent_list)
# df = calculate_overlap(df)

#%%

df.collect()
# %%
import altair as alt

chart1 = (
    alt.Chart(df.collect()).mark_line(point=True)
    .encode(
        x=alt.X(f"{gear_inches_col}:Q").scale(zero=False),
        y=f"{hub_ratio_col}:N",
        color=f"{hub_ratio_col}:N",
    )
)

chart1.interactive()

#%%

combinations_df = (
    combinations
    .with_columns(
        etrto_diameter_mm=etrto_diameter_mm,
        tire_width_mm=tire_width_mm,
        # front_teeth=front_teeth,
        crank_length_mm=crank_length_mm,
        hub_ratio=1,
    )
)

combinations_calc_df = (
    combinations_df
    .transform(polars_gear_calculations)
    .transform(polars_apply_hub_rations, hub_ratio_percent_list)
    .transform(calculate_overlap, ["front_teeth", "rear_teeths"])
    .group_by("front_teeth", "rear_teeths")
    .agg(pl.sum("overlap"), (pl.max("max") / pl.min("min")).alias("range"), pl.max("max"), pl.min("min"))
    # .filter(pl.col("overlap") < 0)
    .filter(pl.col("range") > 3.6)
    .sort("overlap", descending=True)
)

from IPython.display import display
with pl.Config(
    tbl_cols=-1, 
    tbl_rows=50, 
    tbl_width_chars=2000, 
    fmt_str_lengths=2000, 
    fmt_table_cell_list_len=10):
    display(combinations_calc_df.collect())