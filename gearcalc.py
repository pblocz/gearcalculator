#%%
import math

wheel_diameter_col = "Wheel Diameter (mm)"
hub_ration_col = "Hub Ratio (%)"
gear_inches_col = "Gear Inches"
metre_development_col = "Metre Development"
gain_ratio_col = "Gain Ratio"
rear_teeth_col = "Rear Teeth"

def gear_calculations(etrto_diameter_mm, tire_width_mm, front_teeth, rear_teeth, crank_length_mm, hub_ratio=1.0):
    # Constants
    inch_to_mm = 25.4
    mm_to_m = 0.001

    # ETRTO: bead seat diameter (BSD) + 2 * tire height (assumed ~= tire width) + 2.7mm (approx for tyre walls)
    wheel_diameter_mm = etrto_diameter_mm + 2 * tire_width_mm + 2.7
    wheel_diameter_in = wheel_diameter_mm / inch_to_mm
    wheel_circumference_m = math.pi * wheel_diameter_mm * mm_to_m

    # Gear ratio
    gear_ratio = (front_teeth / rear_teeth) * hub_ratio

    # Gear Inches
    gear_inches = gear_ratio * wheel_diameter_in

    # Metre Development
    metre_development = gear_ratio * wheel_circumference_m

    # Gain Ratio
    crank_length_m = crank_length_mm * mm_to_m
    gain_ratio = (wheel_diameter_mm * gear_ratio) / (2 * crank_length_mm)

    return {
        wheel_diameter_col: wheel_diameter_mm,
        hub_ration_col: hub_ratio * 100,
        gear_inches_col: gear_inches,
        metre_development_col: metre_development,
        gain_ratio_col: gain_ratio,
        rear_teeth_col: rear_teeth,
    }


def batch_gear_calculations(etrto_diameter_mm, tire_width_mm, front_teeth, rear_teeth_list, hub_ratio_percent_list, crank_length_mm):
    results = []
    for rear_teeth in rear_teeth_list:
        for hub_percent in hub_ratio_percent_list:
            hub_ratio = hub_percent / 100.0
            result = gear_calculations(
                etrto_diameter_mm,
                tire_width_mm,
                front_teeth,
                rear_teeth,
                crank_length_mm,
                hub_ratio
            )
            results.append(result)
    return results


# Example usage:
# ETRTO size 25-622 (common road tire: 700x25c)
# front: 52T, rear: 14T, crank: 170mm
if __name__ == "__main__":

    results = batch_gear_calculations(
        etrto_diameter_mm=349,
        tire_width_mm=35,
        front_teeth=50,
        rear_teeth_list=[11, 13, 15, 18],
        hub_ratio_percent_list=[64, 100, 157],
        crank_length_mm=170,
    )


    for res in results:
        print(f"Rear: {res['Rear Teeth']}T | "
            f"Hub: {res['Hub Ratio (%)']:.0f}% | "
            f"Gear Inches: {res['Gear Inches']:.2f} | "
            f"Metre Dev: {res['Metre Development']:.2f} m | "
            f"Gain Ratio: {res['Gain Ratio']:.2f}")

