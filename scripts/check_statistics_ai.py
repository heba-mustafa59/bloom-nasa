
"""Run BLOOM Statistics & AI on the supplied annual CSV files.

Does not require metadata_TEMPLATE.json or metadata.json.
Does not modify the CSV files or the scientific modules.
"""

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.trend_analysis import analyze_trend
from modules.mystery_engine import analyze_mystery


def load_csv(filename, value_column):
    path = ROOT / "data" / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Missing file: {path}"
        )

    df = pd.read_csv(path)

    required = {"year", "area_id", value_column}
    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"{filename}: missing columns {missing}"
        )

    df["year"] = pd.to_numeric(
        df["year"], errors="raise"
    )

    df[value_column] = pd.to_numeric(
        df[value_column], errors="raise"
    )

    if (
        df["year"].isna().any()
        or (df["year"] % 1 != 0).any()
    ):
        raise ValueError("Invalid year values")

    if df.duplicated(["area_id", "year"]).any():
        raise ValueError(
            f"{filename}: duplicate area/year pairs"
        )

    if set(df["area_id"].dropna()) != {
        "area_a", "area_b"
    }:
        raise ValueError(
            f"{filename}: unexpected study areas"
        )

    if value_column == "ndvi":
        if not df[value_column].dropna().between(
            -1, 1
        ).all():
            raise ValueError("NDVI out of range")

    if value_column == "rainfall_mm":
        if (df[value_column].dropna() < 0).any():
            raise ValueError("Negative rainfall")

    df["year"] = df["year"].astype(int)

    print(f"\nLoaded: {filename}")
    print(f"Rows: {len(df)}")
    print(
        f"Years: {df['year'].min()}"
        f" - {df['year'].max()}"
    )
    print(
        "Missing measurements:",
        df[value_column].isna().sum()
    )
    print(
        "Rows by area:",
        df.groupby("area_id").size().to_dict()
    )

    return df


def show_trend(label, result):
    print(f"\n{label} TREND")
    print("Status:", result["status"])
    print("Direction:", result["direction"])
    print("Significant:", result["significant"])
    print("Slope/year:", result["slope_per_year"])
    print("Slope/decade:", result["slope_per_decade"])
    print("P-value:", result["p_value"])
    print("Kendall tau:", result["kendall_tau"])
    print("R-squared:", result["r_squared"])
    print("Observations:", result["n_observations"])


def main():
    print("=" * 55)
    print("BLOOM - STATISTICS & AI TEST")
    print("=" * 55)

    ndvi = load_csv(
        "ndvi_annual.csv", "ndvi"
    )

    rainfall = load_csv(
        "rainfall_annual.csv", "rainfall_mm"
    )

    for area_id in ["area_a", "area_b"]:

        print("\n" + "=" * 55)
        print("ANALYZING:", area_id.upper())
        print("=" * 55)

        ndvi_area = ndvi.loc[
            ndvi["area_id"] == area_id
        ].copy()

        rain_area = rainfall.loc[
            rainfall["area_id"] == area_id
        ].copy()

        # 1. NDVI trend
        ndvi_result = analyze_trend(
            ndvi_area,
            "ndvi",
            2005,
            2024
        )

        show_trend("NDVI", ndvi_result)

        # 2. Rainfall trend
        rain_result = analyze_trend(
            rain_area,
            "rainfall_mm",
            2005,
            2024
        )

        show_trend("RAINFALL", rain_result)

        # 3. Mystery machine learning model
        mystery = analyze_mystery(
            ndvi,
            rainfall,
            area_id
        )

        print("\nMYSTERY ENGINE")
        print(
            "Model status:",
            mystery["model_status"]
        )
        print(
            "Validation R2:",
            mystery["validation_r2"]
        )
        print(
            "Validation MAE:",
            mystery["validation_mae"]
        )
        print(
            "Opposing trends:",
            mystery["opposing_trends"]
        )
        print(
            "Anomalies:",
            mystery["anomalies"]
        )
        print(
            "Verdict:",
            mystery["verdict"]
        )

        print("\nLimitations:")
        for item in mystery["limitations"]:
            print("-", item)

    print("\n" + "=" * 55)
    print("ANALYSIS FINISHED")
    print("=" * 55)


if __name__ == "__main__":
    main()
