import streamlit as st
from gearcalc import batch_gear_calculations, hub_ration_col, rear_teeth_col, gear_inches_col, metre_development_col, gain_ratio_col
import polars as pl
import altair as alt

def main():
    front_teeth = st.number_input("Front teeth", value=50)
    rear_teeth = st.text_input("Rear teetch separated by comma", "11,13,15,18")

    rear_teeth_list = [int(t.strip()) for t in rear_teeth.split(",")]

    results = batch_gear_calculations(
        etrto_diameter_mm=349,
        tire_width_mm=35,
        front_teeth=front_teeth,
        rear_teeth_list=rear_teeth_list,
        hub_ratio_percent_list=[64, 100, 157],
        crank_length_mm=170,
    )

    default_results = batch_gear_calculations(
        etrto_diameter_mm=349,
        tire_width_mm=35,
        front_teeth=50,
        rear_teeth_list=[11, 13, 15, 18],
        hub_ratio_percent_list=[64, 100, 157],
        crank_length_mm=170,
    )

    target_col = st.selectbox("Select value column", [gear_inches_col, metre_development_col, gain_ratio_col])

    flat_data = pl.DataFrame(results)
    
    pivot_data = flat_data.pivot(
        on=hub_ration_col,
        index=rear_teeth_col,
        values=[target_col]
    )
    st.dataframe(pivot_data)

    gear_range_max = flat_data.select(pl.max(gain_ratio_col)).item()
    gear_range_min = flat_data.select(pl.min(gain_ratio_col)).item()
    gear_range = gear_range_max / gear_range_min

    st.write(f"Gear range {gear_range * 100:.02f}%")

    chart1 = (
        alt.Chart(flat_data).mark_line(point=True)
        .encode(
            x=alt.X(gear_inches_col).scale(zero=False),
            y=f"{hub_ration_col}:N",
            color=f"{hub_ration_col}:N",
        )
    )
    chart2 = (
        alt.Chart(pl.DataFrame(default_results)).mark_line(point=True)
        .encode(
            x=alt.X(gear_inches_col).scale(zero=False),
            y=f"{hub_ration_col}:N",
            color=f"{hub_ration_col}:N",
        )
    )
    st.altair_chart(
        chart1 & chart2
    )

if __name__ == "__main__":
    main()
