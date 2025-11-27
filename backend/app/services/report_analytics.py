"""
Report Analytics Service - Enhanced Version
Generates robust data analysis and visualizations that never fail.
"""
from __future__ import annotations

import io
import re
from collections import Counter
from datetime import datetime
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np

matplotlib.use("Agg")
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = '#f8f9fa'

# Modern color palette
COLORS = {
    "primary": "#0c5ed7",
    "danger": "#b71c1c",
    "warning": "#fb8c00",
    "success": "#1f8b4c",
    "accent": "#1990ff",
    "muted": "#5f6b7b",
}

SEVERITY_COLORS = ["#4caf50", "#66bb6a", "#fdd835", "#fb8c00", "#b71c1c"]


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in kilometers."""
    import math

    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return R * c


def filter_assaults_by_radius(
    assaults: list[dict[str, Any]], center_lat: float, center_lon: float, radius_km: float
) -> list[dict[str, Any]]:
    """Filter assaults within radius of a point."""
    nearby = []
    for assault in assaults:
        try:
            lat = float(assault.get("latitude", 0))
            lon = float(assault.get("longitude", 0))
            if haversine_distance(center_lat, center_lon, lat, lon) <= radius_km:
                nearby.append(assault)
        except (ValueError, TypeError):
            continue
    return nearby


def parse_assault_date(date_str: str | None) -> datetime | None:
    """Parse assault date string with robust format coverage."""
    if not date_str:
        return None

    raw = str(date_str).strip()
    if not raw:
        return None

    # Normalize common punctuation and remove ordinal suffixes (e.g., "1st", "2nd")
    cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", raw, flags=re.IGNORECASE)
    cleaned = cleaned.replace(",", " ")

    # Drop time component if present (ISO timestamps)
    if "T" in cleaned:
        cleaned = cleaned.split("T", 1)[0]

    cleaned = " ".join(cleaned.split())  # collapse duplicate whitespace

    formats = [
        "%Y %B %d",
        "%Y %b %d",
        "%B %d %Y",
        "%b %d %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%Y-%m-%d",
        "%m-%d-%Y",
        "%m-%d-%y",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%Y/%m/%d",
        "%Y.%m.%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            continue

    try:
        # Last resort: ISO-style parse on the raw value
        return datetime.fromisoformat(raw.split()[0])
    except (ValueError, TypeError):
        return None


def parse_time(time_str: str | None) -> int | None:
    """Parse time string to hour (0-23)."""
    if not time_str:
        return None
    try:
        time_str = str(time_str).strip().lower()
        if "am" in time_str or "pm" in time_str:
            is_pm = "pm" in time_str
            time_part = time_str.replace("am", "").replace("pm", "").strip()
            hour = int(time_part.split(":")[0])
            if is_pm and hour != 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
            return hour
    except (ValueError, AttributeError):
        pass
    return None


def create_time_series_plot(assaults: list[dict[str, Any]]) -> io.BytesIO:
    """Create time series plot - ALWAYS returns a plot."""
    fig, ax = plt.subplots(figsize=(10, 5))

    dates = [parse_assault_date(a.get("event_date")) for a in assaults]
    dates = [d for d in dates if d is not None]

    if not dates:
        ax.text(0.5, 0.5, "Insufficient temporal data for timeline visualization\n\nIncidents recorded but dates not standardized",
                ha="center", va="center", fontsize=12, color=COLORS["muted"],
                bbox=dict(boxstyle='round', facecolor='white', edgecolor=COLORS["primary"], linewidth=2))
        ax.axis("off")
    else:
        df = pd.DataFrame({"date": dates})
        df["month"] = df["date"].dt.to_period("M")
        monthly_counts = df.groupby("month").size().reset_index(name="count")
        monthly_counts["month"] = monthly_counts["month"].dt.to_timestamp()

        ax.plot(monthly_counts["month"], monthly_counts["count"],
                marker="o", linewidth=3, markersize=10, color=COLORS["danger"],
                markerfacecolor=COLORS["danger"], markeredgecolor="white", markeredgewidth=2)
        ax.fill_between(monthly_counts["month"], monthly_counts["count"],
                        alpha=0.2, color=COLORS["danger"])

        ax.set_xlabel("Month", fontsize=12, fontweight="bold", color=COLORS["primary"])
        ax.set_ylabel("Number of Incidents", fontsize=12, fontweight="bold", color=COLORS["primary"])
        ax.set_title("Assault Incidents Over Time", fontsize=14, fontweight="bold", pad=15, color=COLORS["primary"])
        ax.grid(True, alpha=0.3, linestyle="--", linewidth=1)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_color(COLORS["muted"])
        ax.spines["bottom"].set_color(COLORS["muted"])
        plt.xticks(rotation=45, ha="right")

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def create_event_type_breakdown(assaults: list[dict[str, Any]]) -> io.BytesIO:
    """Create pie chart of event types - ALWAYS returns a plot."""
    fig, ax = plt.subplots(figsize=(9, 7))

    event_types = [a.get("event_type") or a.get("event_type_group") or "Unclassified"
                   for a in assaults]
    event_types = [e for e in event_types if e and str(e).strip()]

    if not event_types:
        ax.text(0.5, 0.5, f"Event Classification Data Unavailable\n\n{len(assaults)} total incidents recorded",
                ha="center", va="center", fontsize=12, color=COLORS["muted"],
                bbox=dict(boxstyle='round', facecolor='white', edgecolor=COLORS["warning"], linewidth=2))
        ax.axis("off")
    else:
        type_counts = Counter(event_types)
        # Limit to top 8 categories for clarity
        if len(type_counts) > 8:
            top_types = dict(sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:7])
            other_count = sum(count for typ, count in type_counts.items() if typ not in top_types)
            top_types["Other"] = other_count
            type_counts = top_types

        labels = list(type_counts.keys())
        sizes = list(type_counts.values())
        colors = sns.color_palette("husl", len(labels))

        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct=lambda pct: f'{int(pct/100.*sum(sizes))}\n({pct:.1f}%)',
            startangle=90, colors=colors,
            wedgeprops={"edgecolor": "white", "linewidth": 2.5},
            textprops={'fontsize': 10, 'fontweight': 'bold'}
        )

        for autotext in autotexts:
            autotext.set_color("white")
            autotext.set_fontsize(9)
            autotext.set_fontweight("bold")

        ax.set_title("Incident Classification Breakdown", fontsize=14, fontweight="bold",
                    pad=20, color=COLORS["primary"])

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def create_severity_distribution(assaults: list[dict[str, Any]]) -> io.BytesIO:
    """Create bar chart of severity scores - ALWAYS returns a plot."""
    fig, ax = plt.subplots(figsize=(9, 6))

    severities = []
    for assault in assaults:
        sev = assault.get("severity_score", 1)
        try:
            severities.append(max(1, min(5, int(sev))))
        except (ValueError, TypeError):
            severities.append(1)

    sev_counts = Counter(severities)
    levels = sorted(sev_counts.keys())
    counts = [sev_counts[level] for level in levels]
    colors_for_bars = [SEVERITY_COLORS[min(level - 1, 4)] for level in levels]

    bars = ax.bar(levels, counts, color=colors_for_bars, edgecolor="white", linewidth=2.5, alpha=0.9)

    # Add count labels on bars
    max_count = max(counts) if counts else 0
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, height + 0.5,
                f"{int(height)}", ha="center", va="bottom",
                fontweight="bold", fontsize=11, color=COLORS["primary"])

    ax.set_xlabel("Severity Level (1=Low, 5=Critical)", fontsize=12, fontweight="bold", color=COLORS["primary"])
    ax.set_ylabel("Number of Incidents", fontsize=12, fontweight="bold", color=COLORS["primary"])
    ax.set_title("Incident Severity Distribution", fontsize=14, fontweight="bold", pad=20, color=COLORS["primary"])
    ax.set_xticks(levels)
    ax.set_xticklabels([f"Level {l}" for l in levels])
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Add extra space at top for labels to not collide with title
    if max_count > 0:
        ax.set_ylim(0, max_count * 1.15)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def create_hourly_pattern(assaults: list[dict[str, Any]]) -> io.BytesIO:
    """Create hourly distribution - ALWAYS returns a plot."""
    fig, ax = plt.subplots(figsize=(11, 6))

    hours = [parse_time(a.get("event_time")) for a in assaults]
    hours = [h for h in hours if h is not None]

    if not hours:
        ax.text(0.5, 0.5, f"Time-of-Day Data Not Available\n\n{len(assaults)} incidents with unrecorded times",
                ha="center", va="center", fontsize=12, color=COLORS["muted"],
                bbox=dict(boxstyle='round', facecolor='white', edgecolor=COLORS["accent"], linewidth=2))
        ax.axis("off")
    else:
        hour_counts = Counter(hours)
        all_hours = list(range(24))
        counts = [hour_counts.get(h, 0) for h in all_hours]

        colors_hourly = [COLORS["danger"] if c > np.percentile(counts, 75) else
                        COLORS["warning"] if c > np.percentile(counts, 50) else
                        COLORS["primary"] for c in counts]

        bars = ax.bar(all_hours, counts, color=colors_hourly, edgecolor="white", linewidth=1.5, alpha=0.85)

        ax.set_xlabel("Hour of Day", fontsize=12, fontweight="bold", color=COLORS["primary"])
        ax.set_ylabel("Number of Incidents", fontsize=12, fontweight="bold", color=COLORS["primary"])
        ax.set_title("Incidents by Hour of Day", fontsize=14, fontweight="bold", pad=15, color=COLORS["primary"])
        ax.set_xticks(range(0, 24, 2))
        ax.set_xticklabels([f"{h:02d}:00" for h in range(0, 24, 2)], rotation=45, ha="right")
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def create_injury_statistics(assaults: list[dict[str, Any]]) -> io.BytesIO:
    """Create injury breakdown chart - ALWAYS returns a plot."""
    fig, ax = plt.subplots(figsize=(9, 6))

    total_op = sum(int(a.get("transit_vehicle_operator_injuries", 0) or 0) for a in assaults)
    total_rider = sum(int(a.get("transit_vehicle_rider_injuries", 0) or 0) for a in assaults)
    total_overall = sum(int(a.get("total_injuries", 0) or 0) for a in assaults)

    categories = ["Operator\nInjuries", "Rider\nInjuries", "Total\nInjuries"]
    values = [total_op, total_rider, total_overall]
    colors_bars = [COLORS["danger"], COLORS["warning"], COLORS["muted"]]

    bars = ax.bar(categories, values, color=colors_bars, edgecolor="white", linewidth=2.5, alpha=0.9)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2.0, height + 0.5,
                f"{int(height)}", ha="center", va="bottom",
                fontweight="bold", fontsize=12, color=COLORS["primary"])

    ax.set_ylabel("Total Injuries", fontsize=12, fontweight="bold", color=COLORS["primary"])
    ax.set_title("Injury Statistics Summary", fontsize=14, fontweight="bold", pad=15, color=COLORS["primary"])
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def create_day_of_week_pattern(assaults: list[dict[str, Any]]) -> io.BytesIO:
    """Create day of week distribution."""
    fig, ax = plt.subplots(figsize=(10, 6))

    dates = [parse_assault_date(a.get("event_date")) for a in assaults]
    dates = [d for d in dates if d is not None]

    if not dates:
        ax.text(0.5, 0.5, "Weekly pattern data unavailable",
                ha="center", va="center", fontsize=12, color=COLORS["muted"])
        ax.axis("off")
    else:
        days = [d.strftime("%A") for d in dates]
        day_counts = Counter(days)
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        counts = [day_counts.get(day, 0) for day in day_order]

        colors_days = [COLORS["danger"] if i >= 5 else COLORS["primary"] for i in range(7)]
        bars = ax.bar(range(7), counts, color=colors_days, edgecolor="white", linewidth=2, alpha=0.85)

        ax.set_xticks(range(7))
        ax.set_xticklabels([d[:3] for d in day_order])
        ax.set_ylabel("Number of Incidents", fontsize=12, fontweight="bold", color=COLORS["primary"])
        ax.set_title("Incidents by Day of Week", fontsize=14, fontweight="bold", pad=15, color=COLORS["primary"])
        ax.grid(axis="y", alpha=0.3, linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf


def calculate_stop_safety_metrics(assaults: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate comprehensive safety metrics."""
    total = len(assaults)
    if total == 0:
        return {
            "total_incidents": 0,
            "total_injuries": 0,
            "average_severity": 0,
            "safety_score": 100,
            "risk_level": "LOW",
        }

    total_injuries = sum(int(a.get("total_injuries", 0) or 0) for a in assaults)
    avg_severity = sum(int(a.get("severity_score", 1) or 1) for a in assaults) / total

    safety_score = max(0, 100 - (total * 5) - (avg_severity * 3) - (total_injuries * 2))

    if safety_score >= 70:
        risk_level = "LOW"
    elif safety_score >= 40:
        risk_level = "MODERATE"
    else:
        risk_level = "HIGH"

    return {
        "total_incidents": total,
        "total_injuries": total_injuries,
        "average_severity": round(avg_severity, 2),
        "safety_score": round(safety_score, 1),
        "risk_level": risk_level,
    }


def get_date_range(assaults: list[dict[str, Any]]) -> str:
    """Get the date range of incidents."""
    dates = [parse_assault_date(a.get("event_date")) for a in assaults]
    dates = [d for d in dates if d is not None]

    if not dates:
        return "Date range unavailable"

    dates.sort()
    start, end = dates[0], dates[-1]

    if start.date() == end.date():
        return start.strftime("%B %d, %Y")

    return f"{start.strftime('%B %d, %Y')} - {end.strftime('%B %d, %Y')}"
