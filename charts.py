"""Trend charts for the dashboard: issues over time, and by category.

Both are plain pandas groupby()s over the same dataframe the dashboard
already loaded, so they'll always agree with a manual check against the
database (see TC6 in the project brief).
"""
import matplotlib.pyplot as plt
import pandas as pd

BAR_COLOR = "#3B6E8F"
CATEGORY_COLOR = "#C97B4A"


def _empty_axes(ax, message: str = "No issues logged yet"):
    ax.text(0.5, 0.5, message, ha="center", va="center", fontsize=11, color="gray")
    ax.axis("off")


def issues_over_time_figure(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    if df.empty:
        _empty_axes(ax)
        return fig

    d = df.copy()
    d["date"] = pd.to_datetime(d["timestamp"]).dt.date
    counts = d.groupby("date").size()

    ax.bar(counts.index.astype(str), counts.values, color=BAR_COLOR)
    ax.set_ylabel("Issues logged")
    ax.set_xlabel("Date")
    ax.set_title("Issues over time")
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))
    fig.autofmt_xdate(rotation=45)
    fig.tight_layout()
    return fig


def category_breakdown_figure(df: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(5, 3.6))
    if df.empty:
        _empty_axes(ax)
        return fig

    counts = df["category"].value_counts().sort_values()

    ax.barh(counts.index, counts.values, color=CATEGORY_COLOR)
    ax.set_xlabel("Count")
    ax.set_title("Issues by category")
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    fig.tight_layout()
    return fig