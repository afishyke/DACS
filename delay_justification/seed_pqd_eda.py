from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy.io import loadmat
from scipy.stats import kurtosis, skew


ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "eda_outputs"
PLOTS_DIR = OUTPUT_DIR / "plots"
TABLES_DIR = OUTPUT_DIR / "tables"
REPORTS_DIR = OUTPUT_DIR / "reports"


def ensure_dirs() -> None:
    for directory in [OUTPUT_DIR, PLOTS_DIR, TABLES_DIR, REPORTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def human_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    power = int(math.floor(math.log(size_bytes, 1024)))
    power = min(power, len(units) - 1)
    value = size_bytes / (1024**power)
    return f"{value:.2f} {units[power]}"


def infer_file_type(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    return suffix if suffix else "directory"


def infer_likely_purpose(path: Path) -> str:
    name = path.name
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "Per-class waveform matrix (signals x samples)"
    if suffix == ".mat":
        return "Consolidated tensor for all classes"
    if suffix == ".txt":
        return "Dataset metadata/description"
    return "Unknown"


def build_tree_lines(root: Path, prefix: str = "") -> list[str]:
    children = sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    lines: list[str] = []
    for idx, child in enumerate(children):
        branch = "└── " if idx == len(children) - 1 else "├── "
        lines.append(f"{prefix}{branch}{child.name}")
        if child.is_dir():
            extension = "    " if idx == len(children) - 1 else "│   "
            lines.extend(build_tree_lines(child, prefix + extension))
    return lines


def parse_details(path: Path) -> dict[str, Any]:
    details = {
        "fundamental_hz": None,
        "sampling_hz": None,
        "class_count": None,
        "signals_per_class": None,
        "samples_per_signal": None,
        "duration_ms": None,
        "declared_scale": None,
        "mat_class_order": [],
    }
    if not path.exists():
        return details

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    for line in lines:
        if "Fundamental Frequency" in line:
            match = re.search(r"([\d.]+)", line)
            details["fundamental_hz"] = float(match.group(1)) if match else None
        elif "Sampling Rate" in line:
            match = re.search(r"([\d.]+)\s*kHz", line, re.IGNORECASE)
            if match:
                details["sampling_hz"] = float(match.group(1)) * 1000
            else:
                match = re.search(r"([\d.]+)", line)
                details["sampling_hz"] = float(match.group(1)) if match else None
        elif "Number of Classes" in line:
            match = re.search(r"(\d+)", line)
            details["class_count"] = int(match.group(1)) if match else None
        elif "Signals/Class" in line:
            match = re.search(r"(\d+)", line)
            details["signals_per_class"] = int(match.group(1)) if match else None
        elif "Length of Signal (samples)" in line:
            match = re.search(r"(\d+)", line)
            details["samples_per_signal"] = int(match.group(1)) if match else None
        elif "Length of Signal (time)" in line:
            match = re.search(r"([\d.]+)", line)
            details["duration_ms"] = float(match.group(1)) if match else None
        elif "Amplitude of each Signal" in line:
            details["declared_scale"] = line.split(":", 1)[-1].strip()

        class_match = re.match(r"\s*\d+\.\s+(.+)$", line)
        if class_match:
            details["mat_class_order"].append(class_match.group(1).strip())
    return details


def csv_malformed_stats(path: Path) -> dict[str, int]:
    malformed_rows = 0
    non_numeric_cells = 0
    empty_rows = 0
    expected_cols = None

    with path.open("r", encoding="utf-8", errors="ignore", newline="") as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) == 0:
                empty_rows += 1
                continue
            if expected_cols is None:
                expected_cols = len(row)
            if len(row) != expected_cols:
                malformed_rows += 1
            for cell in row:
                cell = cell.strip()
                if cell == "":
                    continue
                try:
                    float(cell)
                except ValueError:
                    non_numeric_cells += 1

    return {
        "malformed_rows": malformed_rows,
        "non_numeric_cells": non_numeric_cells,
        "empty_rows": empty_rows,
    }


def zero_crossings(signal: np.ndarray) -> int:
    signs = np.sign(signal)
    for idx in range(1, len(signs)):
        if signs[idx] == 0:
            signs[idx] = signs[idx - 1]
    if len(signs) > 1 and signs[0] == 0:
        for idx in range(1, len(signs)):
            if signs[idx] != 0:
                signs[0] = signs[idx]
                break
    return int(np.sum(np.diff(signs) != 0))


def compute_features(signal: np.ndarray, fs: float, f0: float) -> dict[str, float]:
    x = signal.astype(float)
    n = len(x)
    mean_val = float(np.mean(x))
    rms = float(np.sqrt(np.mean(np.square(x))))
    std = float(np.std(x))
    peak_pos = float(np.max(x))
    peak_neg = float(np.min(x))
    p2p = float(peak_pos - peak_neg)
    crest = float(np.max(np.abs(x)) / rms) if rms > 0 else np.nan
    zc = zero_crossings(x)
    duration_s = n / fs if fs else np.nan
    zc_rate = float(zc / duration_s) if duration_s and duration_s > 0 else np.nan
    mean_abs = float(np.mean(np.abs(x)))
    waveform_factor = float(rms / mean_abs) if mean_abs > 0 else np.nan

    skew_val = float(skew(x, bias=False)) if n > 2 else np.nan
    kurt_val = float(kurtosis(x, fisher=True, bias=False)) if n > 3 else np.nan

    spec = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    power = np.abs(spec) ** 2
    total_energy = float(np.sum(power))

    if len(power) > 1:
        dom_idx = int(np.argmax(power[1:]) + 1)
        dominant_freq = float(freqs[dom_idx])
    else:
        dominant_freq = np.nan

    spectral_centroid = float(np.sum(freqs * power) / total_energy) if total_energy > 0 else np.nan
    spectral_spread = (
        float(np.sqrt(np.sum(((freqs - spectral_centroid) ** 2) * power) / total_energy))
        if total_energy > 0
        else np.nan
    )

    fundamental_idx = int(np.argmin(np.abs(freqs - f0)))
    low_idx = max(0, fundamental_idx - 1)
    high_idx = min(len(power), fundamental_idx + 2)
    fundamental_band_energy = float(np.sum(power[low_idx:high_idx]))
    fundamental_band_ratio = float(fundamental_band_energy / total_energy) if total_energy > 0 else np.nan

    hf_mask = freqs >= 500
    high_freq_energy = float(np.sum(power[hf_mask]))
    high_freq_energy_ratio = float(high_freq_energy / total_energy) if total_energy > 0 else np.nan

    diff = np.diff(x)
    derivative_energy = float(np.sum(diff**2) / len(diff)) if len(diff) else np.nan
    local_peak_change = float(np.max(np.abs(diff))) if len(diff) else np.nan

    win = max(5, n // 10)
    win_energies = [float(np.sum(x[i : i + win] ** 2)) for i in range(0, n - win + 1)]
    max_win_energy = max(win_energies) if win_energies else np.nan
    total_win_energy = float(np.sum(win_energies)) if win_energies else np.nan
    transient_energy_proxy = (
        float(max_win_energy / total_win_energy)
        if total_win_energy and total_win_energy > 0
        else np.nan
    )

    return {
        "mean": mean_val,
        "rms": rms,
        "std": std,
        "peak_pos": peak_pos,
        "peak_neg": peak_neg,
        "peak_to_peak": p2p,
        "crest_factor": crest,
        "zero_crossings": zc,
        "zero_crossing_rate_hz": zc_rate,
        "skewness": skew_val,
        "kurtosis": kurt_val,
        "dominant_frequency_hz": dominant_freq,
        "spectral_centroid_hz": spectral_centroid,
        "spectral_spread_hz": spectral_spread,
        "total_spectral_energy": total_energy,
        "fundamental_band_energy": fundamental_band_energy,
        "fundamental_band_ratio": fundamental_band_ratio,
        "high_freq_energy_proxy": high_freq_energy,
        "high_freq_energy_ratio": high_freq_energy_ratio,
        "derivative_energy": derivative_energy,
        "local_peak_change": local_peak_change,
        "transient_energy_proxy": transient_energy_proxy,
        "waveform_factor": waveform_factor,
    }


def save_text(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def to_markdown_table(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def main() -> None:
    sns.set_theme(style="whitegrid", context="talk")
    ensure_dirs()

    root_items = sorted([p for p in ROOT.iterdir() if p.name != "eda_outputs"], key=lambda p: p.name.lower())
    csv_files = sorted([p for p in root_items if p.suffix.lower() == ".csv"], key=lambda p: p.name.lower())
    mat_files = sorted([p for p in root_items if p.suffix.lower() == ".mat"], key=lambda p: p.name.lower())
    txt_files = sorted([p for p in root_items if p.suffix.lower() == ".txt"], key=lambda p: p.name.lower())

    # Stage 1: Inventory
    tree = [ROOT.name + "/"] + build_tree_lines(ROOT)
    save_text(REPORTS_DIR / "stage1_tree.txt", "\n".join(tree))

    manifest_rows = []
    for item in root_items:
        item_type = "folder" if item.is_dir() else infer_file_type(item)
        manifest_rows.append(
            {
                "name": item.name,
                "relative_path": item.name,
                "file_type": item_type,
                "size_bytes": item.stat().st_size if item.is_file() else 0,
                "size_human": human_size(item.stat().st_size) if item.is_file() else "-",
                "likely_purpose": infer_likely_purpose(item),
            }
        )
    manifest_df = pd.DataFrame(manifest_rows).sort_values(by=["file_type", "name"]).reset_index(drop=True)
    manifest_df.to_csv(TABLES_DIR / "dataset_manifest.csv", index=False)

    details_path = ROOT / "Details.txt"
    details = parse_details(details_path)
    fs = float(details["sampling_hz"] or 5000.0)
    f0 = float(details["fundamental_hz"] or 50.0)

    # Stage 2: File-by-file schema and cleanliness
    schema_rows = []
    sample_rows_export = []
    class_data: dict[str, np.ndarray] = {}

    for csv_path in csv_files:
        class_name = csv_path.stem
        malformed = csv_malformed_stats(csv_path)
        try:
            df = pd.read_csv(csv_path, header=None)
        except Exception as err:
            schema_rows.append(
                {
                    "file": csv_path.name,
                    "relative_path": csv_path.name,
                    "shape": "unreadable",
                    "column_count": np.nan,
                    "dtype_summary": "-",
                    "missing_values": np.nan,
                    "duplicate_rows": np.nan,
                    "empty_file": int(csv_path.stat().st_size == 0),
                    "malformed_rows": malformed["malformed_rows"],
                    "non_numeric_cells": malformed["non_numeric_cells"],
                    "notes": f"read failure: {err}",
                }
            )
            continue

        numeric_df = df.apply(pd.to_numeric, errors="coerce")
        class_data[class_name] = numeric_df.to_numpy(dtype=float)

        dtypes = ", ".join(sorted({str(dtype) for dtype in numeric_df.dtypes.tolist()}))
        missing_values = int(numeric_df.isna().sum().sum())
        duplicate_rows = int(numeric_df.duplicated().sum())

        schema_rows.append(
            {
                "file": csv_path.name,
                "relative_path": csv_path.name,
                "shape": f"{numeric_df.shape[0]} x {numeric_df.shape[1]}",
                "column_count": numeric_df.shape[1],
                "dtype_summary": dtypes,
                "missing_values": missing_values,
                "duplicate_rows": duplicate_rows,
                "empty_file": int(csv_path.stat().st_size == 0),
                "malformed_rows": malformed["malformed_rows"],
                "non_numeric_cells": malformed["non_numeric_cells"],
                "notes": "",
            }
        )

        if len(numeric_df) > 0:
            indices = sorted({0, len(numeric_df) // 2, len(numeric_df) - 1})
            for idx in indices:
                sample = numeric_df.iloc[idx, :12].tolist()
                sample_rows_export.append(
                    {
                        "file": csv_path.name,
                        "signal_index": idx,
                        "first_12_samples": json.dumps([round(float(v), 6) for v in sample]),
                    }
                )

    mat_schema_rows = []
    mat_samples_rows = []
    mat_data = None
    mat_var_name = None

    if mat_files:
        mat_path = mat_files[0]
        mat_obj = loadmat(mat_path)
        numeric_vars = {
            k: v
            for k, v in mat_obj.items()
            if not k.startswith("__") and isinstance(v, np.ndarray)
        }
        for key, value in numeric_vars.items():
            mat_schema_rows.append(
                {
                    "file": mat_path.name,
                    "variable": key,
                    "shape": " x ".join(str(dim) for dim in value.shape),
                    "dtype": str(value.dtype),
                    "size": int(value.size),
                }
            )
        candidate = None
        for key, value in numeric_vars.items():
            if value.ndim == 3:
                candidate = (key, value)
                break
        if candidate is None and numeric_vars:
            key = next(iter(numeric_vars))
            candidate = (key, numeric_vars[key])

        if candidate is not None:
            mat_var_name, mat_data = candidate
            missing_values = int(np.isnan(mat_data).sum()) if np.issubdtype(mat_data.dtype, np.floating) else 0
            duplicate_rows = 0
            if mat_data.ndim == 3:
                flattened = np.transpose(mat_data, (2, 0, 1)).reshape(-1, mat_data.shape[1])
                unique_count = np.unique(flattened, axis=0).shape[0]
                duplicate_rows = int(flattened.shape[0] - unique_count)
                probe_indices = [
                    (0, 0),
                    (len(mat_data) // 2, min(mat_data.shape[2] - 1, mat_data.shape[2] // 2)),
                    (len(mat_data) - 1, mat_data.shape[2] - 1),
                ]
                for signal_idx, class_idx in probe_indices:
                    sample = mat_data[signal_idx, :12, class_idx].tolist()
                    mat_samples_rows.append(
                        {
                            "file": mat_path.name,
                            "variable": mat_var_name,
                            "signal_index": signal_idx,
                            "class_index": class_idx,
                            "first_12_samples": json.dumps([round(float(v), 6) for v in sample]),
                        }
                    )

            schema_rows.append(
                {
                    "file": mat_path.name,
                    "relative_path": mat_path.name,
                    "shape": " x ".join(str(dim) for dim in mat_data.shape),
                    "column_count": mat_data.shape[1] if mat_data.ndim > 1 else mat_data.shape[0],
                    "dtype_summary": str(mat_data.dtype),
                    "missing_values": missing_values,
                    "duplicate_rows": duplicate_rows,
                    "empty_file": int(mat_path.stat().st_size == 0),
                    "malformed_rows": 0,
                    "non_numeric_cells": 0,
                    "notes": f"variable: {mat_var_name}",
                }
            )

    schema_df = pd.DataFrame(schema_rows).sort_values("file").reset_index(drop=True)
    schema_df.to_csv(TABLES_DIR / "file_schema_cleanliness.csv", index=False)
    pd.DataFrame(sample_rows_export).to_csv(TABLES_DIR / "csv_sample_rows_first12.csv", index=False)
    pd.DataFrame(mat_schema_rows).to_csv(TABLES_DIR / "mat_variables.csv", index=False)
    pd.DataFrame(mat_samples_rows).to_csv(TABLES_DIR / "mat_sample_signals_first12.csv", index=False)

    # Time-series inferences from actual data
    samples_per_signal = None
    if class_data:
        first_class = next(iter(class_data.values()))
        samples_per_signal = int(first_class.shape[1])

    observed_duration_ms = (samples_per_signal / fs * 1000) if samples_per_signal and fs else np.nan
    dominant_reference_freq = np.nan
    if "Pure_Sinusoidal" in class_data:
        ref = class_data["Pure_Sinusoidal"][0]
        ref_power = np.abs(np.fft.rfft(ref)) ** 2
        ref_freqs = np.fft.rfftfreq(len(ref), 1 / fs)
        if len(ref_power) > 1:
            dominant_reference_freq = float(ref_freqs[np.argmax(ref_power[1:]) + 1])

    global_min = float(min(np.min(arr) for arr in class_data.values())) if class_data else np.nan
    global_max = float(max(np.max(arr) for arr in class_data.values())) if class_data else np.nan

    # Stage 3: Labels and classes
    class_inventory_rows = []
    for class_name, data in sorted(class_data.items(), key=lambda kv: kv[0].lower()):
        class_inventory_rows.append(
            {
                "class_name": class_name,
                "sample_count": int(data.shape[0]),
                "samples_per_signal": int(data.shape[1]),
                "class_type": "compound" if "_with_" in class_name else "pure",
                "mentions_transient": int("Transient" in class_name or class_name == "Notch"),
                "mentions_sag": int("Sag" in class_name),
                "mentions_swell": int("Swell" in class_name),
                "mentions_harmonics": int("Harmonics" in class_name),
                "mentions_flicker": int("Flicker" in class_name),
                "mentions_notch_spike": int("Notch" in class_name),
            }
        )
    class_inventory_df = pd.DataFrame(class_inventory_rows)
    class_inventory_df.to_csv(TABLES_DIR / "class_inventory.csv", index=False)

    balanced = bool(class_inventory_df["sample_count"].nunique() == 1) if not class_inventory_df.empty else False

    # Stage 4: Feature characterization
    feature_rows = []
    for class_name, data in class_data.items():
        for signal_idx, signal in enumerate(data):
            row = {"class_name": class_name, "signal_index": signal_idx}
            row.update(compute_features(signal, fs=fs, f0=f0))
            feature_rows.append(row)
    features_df = pd.DataFrame(feature_rows)
    features_df.to_csv(TABLES_DIR / "signal_features_per_signal.csv", index=False)

    feature_summary = (
        features_df.groupby("class_name")
        .agg(
            {
                "mean": ["mean", "std"],
                "rms": ["mean", "std"],
                "std": ["mean", "std"],
                "peak_pos": ["mean"],
                "peak_neg": ["mean"],
                "peak_to_peak": ["mean"],
                "crest_factor": ["mean"],
                "zero_crossings": ["mean"],
                "skewness": ["mean"],
                "kurtosis": ["mean"],
                "dominant_frequency_hz": ["mean"],
                "spectral_centroid_hz": ["mean"],
                "total_spectral_energy": ["mean"],
                "fundamental_band_ratio": ["mean"],
                "high_freq_energy_ratio": ["mean"],
                "derivative_energy": ["mean"],
                "transient_energy_proxy": ["mean"],
                "waveform_factor": ["mean"],
            }
        )
        .round(6)
    )
    feature_summary.columns = ["_".join([c for c in col if c]) for col in feature_summary.columns.to_flat_index()]
    feature_summary = feature_summary.reset_index().sort_values("class_name")
    feature_summary.to_csv(TABLES_DIR / "feature_summary_by_class.csv", index=False)

    # Stage 5: Transient-oriented separability
    transient_like_classes = sorted([c for c in class_data if ("Transient" in c or c == "Notch")])
    sag_swell_like_classes = sorted([c for c in class_data if (("Sag" in c or "Swell" in c) and "Transient" not in c)])

    transient_metrics = [
        "local_peak_change",
        "transient_energy_proxy",
        "derivative_energy",
        "spectral_spread_hz",
        "high_freq_energy_ratio",
    ]

    separation_rows = []
    if transient_like_classes and sag_swell_like_classes:
        transient_group = features_df[features_df["class_name"].isin(transient_like_classes)]
        sustained_group = features_df[features_df["class_name"].isin(sag_swell_like_classes)]
        for metric in transient_metrics:
            t_vals = transient_group[metric].dropna().to_numpy()
            s_vals = sustained_group[metric].dropna().to_numpy()
            t_mean = float(np.mean(t_vals))
            s_mean = float(np.mean(s_vals))
            t_std = float(np.std(t_vals, ddof=1)) if len(t_vals) > 1 else np.nan
            s_std = float(np.std(s_vals, ddof=1)) if len(s_vals) > 1 else np.nan
            pooled = np.sqrt(((t_std**2) + (s_std**2)) / 2) if np.isfinite(t_std) and np.isfinite(s_std) else np.nan
            cohens_d = float((t_mean - s_mean) / pooled) if pooled and pooled > 0 else np.nan
            separation_rows.append(
                {
                    "feature": metric,
                    "transient_group_mean": t_mean,
                    "sag_swell_group_mean": s_mean,
                    "cohens_d": cohens_d,
                }
            )
    separation_df = pd.DataFrame(separation_rows)
    separation_df.to_csv(TABLES_DIR / "transient_vs_sagswell_separation.csv", index=False)

    class_transient_proxy = (
        features_df.groupby("class_name")[transient_metrics]
        .mean()
        .pipe(lambda x: (x - x.mean()) / x.std(ddof=0))
        .fillna(0)
    )
    class_transient_proxy["transient_score"] = class_transient_proxy.sum(axis=1)
    class_transient_proxy = class_transient_proxy.sort_values("transient_score", ascending=False)
    class_transient_proxy.to_csv(TABLES_DIR / "class_transient_scores.csv")

    # Consistency checks: CSV vs MAT class order when possible
    mat_csv_alignment_rows = []
    if mat_data is not None and mat_data.ndim == 3 and details.get("mat_class_order"):
        class_order = details["mat_class_order"]
        for idx, class_name in enumerate(class_order):
            if class_name not in class_data or idx >= mat_data.shape[2]:
                continue
            csv_arr = class_data[class_name]
            mat_arr = mat_data[:, :, idx]
            same_shape = csv_arr.shape == mat_arr.shape
            max_abs_diff = float(np.max(np.abs(csv_arr - mat_arr))) if same_shape else np.nan
            mat_csv_alignment_rows.append(
                {
                    "class_name": class_name,
                    "mat_class_index": idx,
                    "same_shape": int(same_shape),
                    "max_abs_diff": max_abs_diff,
                    "exact_match": int(same_shape and np.allclose(csv_arr, mat_arr, atol=1e-12)),
                }
            )
    mat_csv_alignment_df = pd.DataFrame(mat_csv_alignment_rows)
    mat_csv_alignment_df.to_csv(TABLES_DIR / "mat_csv_alignment.csv", index=False)

    # Plots
    time_axis_ms = np.arange(samples_per_signal) / fs * 1000 if samples_per_signal else np.array([])

    # Representative signals by class
    classes_sorted = sorted(class_data)
    cols = 3
    rows = int(math.ceil(len(classes_sorted) / cols))
    fig, axes = plt.subplots(rows, cols, figsize=(22, rows * 3.2), sharex=True)
    axes = np.array(axes).reshape(rows, cols)
    for idx, class_name in enumerate(classes_sorted):
        r = idx // cols
        c = idx % cols
        ax = axes[r, c]
        data = class_data[class_name]
        ref_signal = data[len(data) // 2]
        ax.plot(time_axis_ms, ref_signal, lw=1.6, color="#1f77b4")
        ax.set_title(class_name, fontsize=11)
        ax.set_ylabel("Amplitude")
        ax.set_xlabel("Time (ms)")
    for idx in range(len(classes_sorted), rows * cols):
        r = idx // cols
        c = idx % cols
        axes[r, c].axis("off")
    fig.suptitle("Representative signal per class (middle sample)", y=1.01)
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "representative_signals_per_class.png", dpi=240, bbox_inches="tight")
    plt.close(fig)

    def overlay_plot(classes: list[str], title: str, filename: str) -> None:
        fig, ax = plt.subplots(figsize=(12, 5.5))
        palette = sns.color_palette("tab10", n_colors=len(classes))
        for color, class_name in zip(palette, classes):
            if class_name not in class_data:
                continue
            signal = class_data[class_name][len(class_data[class_name]) // 2]
            ax.plot(time_axis_ms, signal, label=class_name, linewidth=2.0, alpha=0.95, color=color)
        ax.set_title(title)
        ax.set_xlabel("Time (ms)")
        ax.set_ylabel("Amplitude")
        ax.legend(loc="best", ncol=2, fontsize=9)
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / filename, dpi=260, bbox_inches="tight")
        plt.close(fig)

    overlay_plot(
        ["Pure_Sinusoidal", "Transient", "Oscillatory_Transient", "Sag_with_Oscillatory_Transient", "Swell_with_Oscillatory_Transient", "Notch"],
        "Transient-like and oscillatory classes vs reference",
        "overlay_transient_related_classes.png",
    )
    overlay_plot(
        ["Pure_Sinusoidal", "Sag", "Swell", "Interruption", "Sag_with_Harmonics", "Swell_with_Harmonics"],
        "Sag/swell sustained disturbances vs reference",
        "overlay_sag_swell_related_classes.png",
    )
    overlay_plot(
        ["Pure_Sinusoidal", "Harmonics", "Harmonics_with_Sag", "Harmonics_with_Swell", "Flicker", "Flicker_with_Sag", "Flicker_with_Swell"],
        "Harmonics/flicker contamination vs reference",
        "overlay_harmonics_flicker_related_classes.png",
    )

    # Transient metrics distributions
    for metric in transient_metrics:
        fig, ax = plt.subplots(figsize=(14, 6))
        sns.boxplot(
            data=features_df,
            x="class_name",
            y=metric,
            order=class_transient_proxy.index.tolist(),
            ax=ax,
            showfliers=False,
        )
        ax.set_title(f"{metric} distribution by class (ordered by transient score)")
        ax.set_xlabel("Class")
        ax.set_ylabel(metric)
        ax.tick_params(axis="x", rotation=65)
        fig.tight_layout()
        fig.savefig(PLOTS_DIR / f"metric_{metric}_by_class.png", dpi=240, bbox_inches="tight")
        plt.close(fig)

    # Combined scatter for transient separability
    fig, ax = plt.subplots(figsize=(10, 7))
    scatter_df = features_df.copy()
    scatter_df["group"] = np.where(
        scatter_df["class_name"].isin(transient_like_classes),
        "transient_like",
        np.where(scatter_df["class_name"].isin(sag_swell_like_classes), "sag_swell_like", "other"),
    )
    sns.scatterplot(
        data=scatter_df,
        x="derivative_energy",
        y="spectral_spread_hz",
        hue="group",
        style="group",
        alpha=0.35,
        s=22,
        ax=ax,
    )
    ax.set_title("Transient-like vs sag/swell-like separability (all signals)")
    fig.tight_layout()
    fig.savefig(PLOTS_DIR / "scatter_transient_vs_sagswell_derivative_vs_spectralspread.png", dpi=260, bbox_inches="tight")
    plt.close(fig)

    # Report snippets
    label_encoding_notes = {
        "folder_names": False,
        "filenames": True,
        "metadata_table": details_path.exists(),
        "separate_label_file": False,
    }

    # Stage 6 reports
    executive_summary_lines = [
        "# A. Executive summary",
        "",
        f"- Inventory confirms {len(csv_files)} CSV class files, {len(mat_files)} MAT file, and {len(txt_files)} TXT metadata file.",
        f"- Classes are encoded directly in CSV filenames (exactly {len(class_data)} class names).",
        f"- Each CSV has shape {samples_per_signal and class_data[next(iter(class_data))].shape[0]} x {samples_per_signal}; sample counts are {'balanced' if balanced else 'not balanced'}.",
        f"- Global amplitude range observed in waveform files: [{global_min:.6f}, {global_max:.6f}] (supports scaled/synthetic signal claim).",
        f"- With fs={fs:.0f} Hz and {samples_per_signal} samples/signal, each signal spans {observed_duration_ms:.3f} ms (~1 cycle at {f0:.0f} Hz).",
        "- Transient-oriented features indicate strongest abrupt/localized behavior in classes containing Transient and in Notch; sag/swell classes look more sustained in-window.",
    ]
    save_text(REPORTS_DIR / "A_executive_summary.md", "\n".join(executive_summary_lines))

    structure_lines = [
        "# B. Dataset structure report",
        "",
        "## Tree",
        "```text",
        *tree,
        "```",
        "",
        "## Manifest (from extracted root)",
        to_markdown_table(manifest_df),
        "",
        "## Label encoding detection",
        f"- folder names: {label_encoding_notes['folder_names']}",
        f"- filenames: {label_encoding_notes['filenames']}",
        f"- metadata table (Details.txt): {label_encoding_notes['metadata_table']}",
        f"- separate label file: {label_encoding_notes['separate_label_file']}",
        "",
        "## File schema and cleanliness",
        to_markdown_table(schema_df),
        "",
        f"Detailed samples saved: `{TABLES_DIR / 'csv_sample_rows_first12.csv'}` and `{TABLES_DIR / 'mat_sample_signals_first12.csv'}`.",
    ]
    save_text(REPORTS_DIR / "B_dataset_structure_report.md", "\n".join(structure_lines))

    class_lines = [
        "# C. Class inventory report",
        "",
        "## Exact class list (from filenames)",
        *[f"- {name}" for name in sorted(class_data)],
        "",
        "## Counts and class type",
        to_markdown_table(class_inventory_df.sort_values("class_name")),
        "",
        f"- Balanced dataset by class counts: {balanced}",
        f"- Pure class count: {int((class_inventory_df['class_type'] == 'pure').sum())}",
        f"- Compound class count: {int((class_inventory_df['class_type'] == 'compound').sum())}",
        "",
        "## Cautious name-based disturbance relevance (inference from names only)",
        "- transient behavior: classes containing `Transient` plus `Notch`",
        "- sustained undervoltage/sag: classes containing `Sag`",
        "- sustained overvoltage/swell: classes containing `Swell`",
        "- harmonic distortion: classes containing `Harmonics`",
        "- flicker: classes containing `Flicker`",
        "- notch/spike behavior: class `Notch`",
    ]
    save_text(REPORTS_DIR / "C_class_inventory_report.md", "\n".join(class_lines))

    quality_lines = [
        "# D. Signal quality / cleanliness report",
        "",
        f"- Empty files detected: {int((schema_df['empty_file'] == 1).sum())}",
        f"- Total malformed CSV rows: {int(schema_df[schema_df['file'].str.endswith('.csv', na=False)]['malformed_rows'].sum())}",
        f"- Total non-numeric CSV cells: {int(schema_df[schema_df['file'].str.endswith('.csv', na=False)]['non_numeric_cells'].sum())}",
        f"- Total missing values across data-bearing files: {int(schema_df['missing_values'].fillna(0).sum())}",
        f"- Total duplicate signal rows across CSV files (sum): {int(schema_df[schema_df['file'].str.endswith('.csv', na=False)]['duplicate_rows'].sum())}",
        "",
        "## Time-series schema facts",
        f"- samples per signal: {samples_per_signal}",
        f"- inferred duration per signal from fs: {observed_duration_ms:.3f} ms",
        f"- dominant frequency check on Pure_Sinusoidal reference: {dominant_reference_freq:.3f} Hz",
        f"- observed amplitude min/max across CSV signals: [{global_min:.6f}, {global_max:.6f}]",
        "- Interpretation: waveform values are scaled (dimensionless), not raw volts.",
    ]
    save_text(REPORTS_DIR / "D_signal_quality_cleanliness_report.md", "\n".join(quality_lines))

    transient_lines = [
        "# E. Transient-analysis report",
        "",
        "## Candidate transient-like classes",
        *(f"- {name}" for name in transient_like_classes),
        "",
        "## Candidate sag/swell-like sustained classes",
        *(f"- {name}" for name in sag_swell_like_classes),
        "",
        "## Feature-based separability (grouped)",
        to_markdown_table(separation_df.round(6)) if not separation_df.empty else "No separability table generated.",
        "",
        "## Class transient score ranking",
        to_markdown_table(class_transient_proxy.reset_index().rename(columns={"index": "class_name"}).round(6)),
        "",
        "## One-cycle limitation",
        "- Each signal is one 50 Hz cycle (20 ms), so only within-cycle abruptness can be assessed robustly.",
        "- Multi-cycle persistence, event duration beyond 20 ms, and recovery dynamics cannot be claimed from this dataset alone.",
        "- Suitable hardware-delay features should emphasize local energy bursts and derivative peaks inside short windows, not long-horizon persistence.",
    ]
    save_text(REPORTS_DIR / "E_transient_analysis_report.md", "\n".join(transient_lines))

    next_lines = [
        "# F. Recommended next analyses",
        "",
        "1. Build publication-ready figure set with consistent panel annotations and class-colored overlays.",
        "2. Quantify transient-vs-sustained separability with confidence intervals per feature.",
        "3. Derive hardware-delay-oriented feature candidates using causal short windows (e.g., 1 ms, 2 ms, 4 ms).",
        "4. Stress-test class definitions by checking mislabeled/outlier signals in high-transient-score tails.",
        "5. Prepare classifier-ready preprocessing only after label and windowing assumptions are frozen.",
    ]
    save_text(REPORTS_DIR / "F_recommended_next_analyses.md", "\n".join(next_lines))

    # Master JSON summary for reproducibility
    summary_payload = {
        "root": str(ROOT),
        "output_dir": str(OUTPUT_DIR),
        "sampling_hz": fs,
        "fundamental_hz": f0,
        "samples_per_signal": samples_per_signal,
        "duration_ms": observed_duration_ms,
        "class_count": len(class_data),
        "balanced": balanced,
        "transient_like_classes": transient_like_classes,
        "sag_swell_like_classes": sag_swell_like_classes,
        "label_encoding": label_encoding_notes,
    }
    save_text(OUTPUT_DIR / "summary.json", json.dumps(summary_payload, indent=2))

    print(f"EDA complete. Outputs saved under: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
