#!/usr/bin/env python3

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DATA_DIR = Path("/home/abhishek/DACS/data/archive (2)")
OUTPUT_IMAGE = DATA_DIR / "linkedin_voltage_frequency_dashboard.png"
OUTPUT_TIMES = DATA_DIR / "all_fluctuation_times.csv"
OUTPUT_MAJOR_WINDOWS = DATA_DIR / "major_fluctuation_windows.csv"

VOLTAGE_LOW = 207.0
VOLTAGE_HIGH = 253.0
FREQ_LOW = 49.5
FREQ_HIGH = 50.5


def add_aggregate(current: pd.DataFrame | None, update: pd.DataFrame) -> pd.DataFrame:
    update = update.astype("int64")
    if current is None:
        return update
    return current.add(update, fill_value=0)


def get_detail_csv_files() -> list[Path]:
    required = {"x_Timestamp", "z_Avg Voltage (Volt)", "y_Freq (Hz)"}
    detail_files: list[Path] = []

    for csv_path in sorted(DATA_DIR.glob("*.csv")):
        try:
            cols = set(pd.read_csv(csv_path, nrows=0).columns)
            if required.issubset(cols):
                detail_files.append(csv_path)
        except Exception:
            continue

    return detail_files


def process_data(files: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    daily_agg = None
    monthly_agg = None
    hourly_agg = None
    timestamp_agg = None

    use_cols = ["x_Timestamp", "z_Avg Voltage (Volt)", "y_Freq (Hz)"]

    for csv_path in files:
        print(f"Processing: {csv_path.name}")
        for chunk in pd.read_csv(csv_path, usecols=use_cols, chunksize=500_000):
            ts = pd.to_datetime(chunk["x_Timestamp"], errors="coerce")
            v = pd.to_numeric(chunk["z_Avg Voltage (Volt)"], errors="coerce")
            f = pd.to_numeric(chunk["y_Freq (Hz)"], errors="coerce")

            valid = ts.notna()
            if not valid.any():
                continue

            ts = ts[valid].dt.floor("3min")
            v = v[valid]
            f = f[valid]

            v_missing = v.isna() | (v <= 0)
            f_missing = f.isna() | (f <= 0)

            v_fluctuation = v_missing | ((~v_missing) & ((v < VOLTAGE_LOW) | (v > VOLTAGE_HIGH)))
            f_fluctuation = f_missing | ((~f_missing) & ((f < FREQ_LOW) | (f > FREQ_HIGH)))

            temp = pd.DataFrame(
                {
                    "timestamp": ts,
                    "date": ts.dt.normalize(),
                    "year_month": ts.dt.to_period("M").astype(str),
                    "hour": ts.dt.hour,
                    "total": 1,
                    "v_fluc": v_fluctuation.astype("int8"),
                    "f_fluc": f_fluctuation.astype("int8"),
                }
            )
            temp["both_fluc"] = (temp["v_fluc"] & temp["f_fluc"]).astype("int8")

            daily_agg = add_aggregate(
                daily_agg,
                temp.groupby("date")[["total", "v_fluc", "f_fluc", "both_fluc"]].sum(),
            )
            monthly_agg = add_aggregate(
                monthly_agg,
                temp.groupby("year_month")[["total", "v_fluc", "f_fluc", "both_fluc"]].sum(),
            )
            hourly_agg = add_aggregate(
                hourly_agg,
                temp.groupby("hour")[["total", "v_fluc", "f_fluc", "both_fluc"]].sum(),
            )
            timestamp_agg = add_aggregate(
                timestamp_agg,
                temp.groupby("timestamp")[["total", "v_fluc", "f_fluc", "both_fluc"]].sum(),
            )

    daily = daily_agg.sort_index().astype("int64")
    monthly = monthly_agg.sort_index().astype("int64")
    hourly = hourly_agg.sort_index().astype("int64")
    by_timestamp = timestamp_agg.sort_index().astype("int64")

    for frame in [daily, monthly, hourly, by_timestamp]:
        frame["v_rate"] = frame["v_fluc"] / frame["total"] * 100.0
        frame["f_rate"] = frame["f_fluc"] / frame["total"] * 100.0
        frame["both_rate"] = frame["both_fluc"] / frame["total"] * 100.0

    return daily, monthly, hourly, by_timestamp


def build_major_windows(by_timestamp: pd.DataFrame) -> pd.DataFrame:
    v_threshold = by_timestamp["v_rate"].quantile(0.90)
    f_threshold = by_timestamp["f_rate"].quantile(0.90)

    major = by_timestamp[
        (by_timestamp["v_rate"] >= v_threshold) | (by_timestamp["f_rate"] >= f_threshold)
    ][["v_rate", "f_rate", "both_rate"]].copy()

    if major.empty:
        return pd.DataFrame()

    major = major.reset_index().rename(columns={"index": "timestamp"})
    major["new_event"] = major["timestamp"].diff().gt(pd.Timedelta(minutes=3)).fillna(True)
    major["event_id"] = major["new_event"].cumsum()

    windows = major.groupby("event_id").agg(
        start=("timestamp", "min"),
        end=("timestamp", "max"),
        intervals=("timestamp", "size"),
        peak_voltage_rate=("v_rate", "max"),
        peak_frequency_rate=("f_rate", "max"),
        avg_voltage_rate=("v_rate", "mean"),
        avg_frequency_rate=("f_rate", "mean"),
        peak_both_rate=("both_rate", "max"),
    )

    windows["duration_minutes"] = windows["intervals"] * 3
    windows["duration_hours"] = windows["duration_minutes"] / 60.0
    windows["peak_combined_rate"] = windows[["peak_voltage_rate", "peak_frequency_rate"]].max(axis=1)
    windows = windows.sort_values(["peak_combined_rate", "duration_minutes"], ascending=[False, False])
    return windows


def save_times_csv(by_timestamp: pd.DataFrame) -> None:
    out = by_timestamp.copy().reset_index().rename(columns={"index": "timestamp"})
    out["voltage_fluctuated"] = out["v_fluc"] > 0
    out["frequency_fluctuated"] = out["f_fluc"] > 0
    out["any_fluctuation"] = out["voltage_fluctuated"] | out["frequency_fluctuated"]
    out["simultaneous_fluctuation"] = out["voltage_fluctuated"] & out["frequency_fluctuated"]

    out = out[
        [
            "timestamp",
            "total",
            "v_fluc",
            "f_fluc",
            "both_fluc",
            "v_rate",
            "f_rate",
            "both_rate",
            "voltage_fluctuated",
            "frequency_fluctuated",
            "any_fluctuation",
            "simultaneous_fluctuation",
        ]
    ]
    out.to_csv(OUTPUT_TIMES, index=False)


def create_dashboard(
    daily: pd.DataFrame,
    monthly: pd.DataFrame,
    hourly: pd.DataFrame,
    major_windows: pd.DataFrame,
    files: list[Path],
) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig = plt.figure(figsize=(18, 11), dpi=220)
    gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.18)

    # Panel 1: Daily rates
    ax1 = fig.add_subplot(gs[0, 0])
    daily_plot = daily.copy()
    daily_plot.index = pd.to_datetime(daily_plot.index)
    daily_plot["v_roll"] = daily_plot["v_rate"].rolling(14, min_periods=1).mean()
    daily_plot["f_roll"] = daily_plot["f_rate"].rolling(14, min_periods=1).mean()

    ax1.plot(daily_plot.index, daily_plot["v_rate"], color="#f28e2b", alpha=0.20, linewidth=1)
    ax1.plot(daily_plot.index, daily_plot["f_rate"], color="#4e79a7", alpha=0.25, linewidth=1)
    ax1.plot(daily_plot.index, daily_plot["v_roll"], color="#d55e00", linewidth=2.3, label="Voltage fluctuation rate")
    ax1.plot(daily_plot.index, daily_plot["f_roll"], color="#1f77b4", linewidth=2.3, label="Frequency fluctuation rate")
    ax1.set_title("Daily Fluctuation Rate (14-day smoothed)", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Readings fluctuating (%)")
    ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax1.tick_params(axis="x", rotation=30)
    ax1.legend(frameon=True, fontsize=9)

    # Panel 2: Monthly comparison
    ax2 = fig.add_subplot(gs[0, 1])
    month_plot = monthly.copy()
    month_plot.index = pd.to_datetime(month_plot.index)
    x = np.arange(len(month_plot))
    w = 0.42
    ax2.bar(x - w / 2, month_plot["v_rate"], width=w, color="#e15759", label="Voltage")
    ax2.bar(x + w / 2, month_plot["f_rate"], width=w, color="#4e79a7", label="Frequency")
    ax2.set_title("Monthly Fluctuation Rate", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Readings fluctuating (%)")
    tick_idx = np.arange(0, len(month_plot), 2)
    ax2.set_xticks(tick_idx)
    ax2.set_xticklabels([month_plot.index[i].strftime("%b\n%Y") for i in tick_idx], fontsize=8)
    ax2.legend(frameon=True, fontsize=9)

    # Panel 3: Hourly profile
    ax3 = fig.add_subplot(gs[1, 0])
    hour_plot = hourly.sort_index()
    ax3.plot(hour_plot.index, hour_plot["v_rate"], marker="o", color="#d55e00", linewidth=2, label="Voltage")
    ax3.plot(hour_plot.index, hour_plot["f_rate"], marker="o", color="#1f77b4", linewidth=2, label="Frequency")
    ax3.set_title("Average Fluctuation by Hour of Day", fontsize=12, fontweight="bold")
    ax3.set_xlabel("Hour")
    ax3.set_ylabel("Readings fluctuating (%)")
    ax3.set_xticks(range(0, 24, 2))
    ax3.legend(frameon=True, fontsize=9)

    # Panel 4: Top severe windows
    ax4 = fig.add_subplot(gs[1, 1])
    if major_windows.empty:
        ax4.text(0.5, 0.5, "No major fluctuation windows found", ha="center", va="center", fontsize=11)
        ax4.axis("off")
    else:
        top = major_windows.head(10).copy()
        labels = [s.strftime("%d %b %Y\n%H:%M") for s in top["start"]]
        y = np.arange(len(top))
        bars = ax4.barh(y, top["duration_hours"], color="#76b7b2")
        ax4.set_yticks(y)
        ax4.set_yticklabels(labels, fontsize=8)
        ax4.invert_yaxis()
        ax4.set_xlabel("Window duration (hours)")
        ax4.set_title("Top 10 Major Fluctuation Windows", fontsize=12, fontweight="bold")

        for i, (_, row) in enumerate(top.iterrows()):
            txt = f"V:{row['peak_voltage_rate']:.0f}%  F:{row['peak_frequency_rate']:.0f}%"
            ax4.text(row["duration_hours"] + 0.02, i, txt, va="center", fontsize=8)

    total_records = int(daily["total"].sum())
    v_overall = daily["v_fluc"].sum() / daily["total"].sum() * 100.0
    f_overall = daily["f_fluc"].sum() / daily["total"].sum() * 100.0
    both_overall = daily["both_fluc"].sum() / daily["total"].sum() * 100.0

    file_list = ", ".join([f.name for f in files])
    title = "Voltage & Frequency Fluctuation Dashboard (All CSV Meter Data: 2019-2021)"
    subtitle = (
        f"Thresholds: Voltage outside {VOLTAGE_LOW:.0f}-{VOLTAGE_HIGH:.0f}V, "
        f"Frequency outside {FREQ_LOW:.1f}-{FREQ_HIGH:.1f}Hz, including zero/no-signal values"
    )
    summary = (
        f"Total readings analyzed: {total_records:,}  |  "
        f"Voltage fluctuation: {v_overall:.2f}%  |  "
        f"Frequency fluctuation: {f_overall:.2f}%  |  "
        f"Simultaneous fluctuation: {both_overall:.2f}%"
    )

    fig.suptitle(title, fontsize=16, fontweight="bold", y=0.98)
    fig.text(0.5, 0.945, subtitle, ha="center", fontsize=10)
    fig.text(0.5, 0.015, summary, ha="center", fontsize=10, fontweight="bold")
    fig.text(0.5, 0.001, f"Sources: {file_list}", ha="center", fontsize=7)

    plt.savefig(OUTPUT_IMAGE, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    files = get_detail_csv_files()
    if not files:
        raise SystemExit("No CSV files with voltage and frequency columns found.")

    daily, monthly, hourly, by_timestamp = process_data(files)
    save_times_csv(by_timestamp)

    major_windows = build_major_windows(by_timestamp)
    major_windows.to_csv(OUTPUT_MAJOR_WINDOWS, index=False)

    create_dashboard(daily, monthly, hourly, major_windows, files)

    print("Done.")
    print(f"Chart: {OUTPUT_IMAGE}")
    print(f"All fluctuation times: {OUTPUT_TIMES}")
    print(f"Major windows: {OUTPUT_MAJOR_WINDOWS}")


if __name__ == "__main__":
    main()
