"""Matplotlib charts for the TERRA ALERT analysis dashboard"""

import io
from collections import defaultdict

from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

BG = "#0b1728"
PANEL = "#101f32"
TEXT = "#e8f3ff"
MUTED = "#91a8c0"
GRID = "#29415b"
PALETTE = [
    "#36baff", "#36e3b1", "#ffb454", "#b79cff", "#ff718d",
    "#65d6ce", "#f2d35e", "#8daeff", "#e58bd7", "#a9df76",
    "#ff9466", "#72c7ff", "#c5a3ff", "#64dba0", "#ffcc80",
]

METRICS = {
    "records": {"column": None, "label": "Registros", "short": "registros"},
    "deaths": {"column": "Total Deaths", "label": "Fallecimientos", "short": "fallecimientos"},
    "affected": {"column": "Total Affected", "label": "Personas afectadas", "short": "personas afectadas"},
}


def _metric_value(row, metric):
    if metric == "records":
        return 1.0
    column = METRICS.get(metric, METRICS["records"])["column"]
    raw = row.get(column)
    if raw is None or str(raw).strip() in ("", "nan", "NaN", "None"):
        return None
    try:
        return float(str(raw).strip().replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _figure(title, xlabel="", ylabel="", figsize=(10, 4.8)):
    fig = Figure(figsize=figsize, facecolor=BG)
    ax = fig.subplots()
    ax.set_facecolor(BG)
    ax.set_title(title, color=TEXT, pad=17, fontsize=13, fontweight="bold")
    if xlabel:
        ax.set_xlabel(xlabel, color=MUTED, labelpad=9)
    if ylabel:
        ax.set_ylabel(ylabel, color=MUTED, labelpad=9)
    ax.tick_params(colors=MUTED, labelsize=9)
    ax.grid(alpha=.18, color="white", axis="y", linestyle="--", linewidth=.7)
    for spine in ax.spines.values():
        spine.set_color(GRID)
    return fig, ax


def _format_axis(ax, metric):
    if metric in ("deaths", "affected"):
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", ".")))


def _format_bar_axis(ax, metric):
    ax.grid(False, axis="y")
    ax.grid(True, axis="x", alpha=.18, color="white", linestyle="--", linewidth=.7)
    if metric in ("deaths", "affected"):
        ax.xaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}".replace(",", ".")))


def _png(fig):
    output = io.BytesIO()
    fig.tight_layout(pad=2)
    fig.savefig(output, format="png", dpi=145, facecolor=fig.get_facecolor(), bbox_inches="tight")
    output.seek(0)
    return output


def _filter_years(data, start, end):
    return [row for row in data if start <= row.get("year", 0) <= end]


def create_multi_series_graph(data, selected, group="type", metric="records", start=1900, end=2025, scale="linear"):
    """Compare multiple disaster types or countries over time."""
    metric = metric if metric in METRICS else "records"
    group_column = "Disaster Type" if group == "type" else "Country"
    rows = _filter_years(data, start, end)
    selected_set = set(selected or [])
    if selected_set:
        rows = [r for r in rows if r.get(group_column, "").strip() in selected_set]

    # Keep the graph legible if a user selects every available item.
    grouped = defaultdict(lambda: defaultdict(float))
    for row in rows:
        name = row.get(group_column, "").strip() or "Sin especificar"
        value = _metric_value(row, metric)
        if value is not None:
            grouped[name][row["year"]] += value

    # Preserve the user's selection and order.
    if selected_set:
        ordered_names = [name for name in selected if name in grouped]
    else:
        ordered_names = sorted(grouped, key=lambda name: sum(grouped[name].values()), reverse=True)
        default_limit = 8 if group == "country" else 5
        ordered_names = ordered_names[:default_limit]

    group_label = "tipo de desastre" if group == "type" else "país"
    metric_label = METRICS[metric]["label"]
    fig, ax = _figure(
        f"Evolución comparada por {group_label}",
        "Año", metric_label, (11, 5.2)
    )
    years = list(range(start, end + 1))
    if not ordered_names:
        ax.text(.5, .5, "No hay datos para esta selección", color=MUTED, ha="center", va="center", transform=ax.transAxes)
    else:
        for index, name in enumerate(ordered_names):
            if metric == "records":
                values = [grouped[name].get(year, 0) for year in years]
            else:
                # A year with no reported impact value is unknown, not zero.
                values = [grouped[name].get(year) for year in years]
            ax.plot(
                years, values, label=name, color=PALETTE[index % len(PALETTE)],
                linewidth=2.35, alpha=.98, solid_capstyle="round"
            )
        legend = ax.legend(
            loc="upper left", bbox_to_anchor=(1.01, 1), frameon=False,
            labelcolor=TEXT, fontsize=8, title=group_label.title(),
            title_fontsize=9, handlelength=2.4, labelspacing=.8
        )
        legend.get_title().set_color(TEXT)
    if scale == "log":
        ax.set_yscale("symlog", linthresh=1)
    _format_axis(ax, metric)
    ax.margins(x=.015)
    return _png(fig)


def create_country_detail_graph(data, country, metric="records", start=1900, end=2025, disaster_type=""):
    metric = metric if metric in METRICS else "records"
    rows = [r for r in _filter_years(data, start, end) if r.get("Country", "").strip() == country]
    if disaster_type:
        rows = [r for r in rows if r.get("Disaster Type", "").strip() == disaster_type]
    annual = defaultdict(float)
    for row in rows:
        value = _metric_value(row, metric)
        if value is not None:
            annual[row["year"]] += value
    years = list(range(start, end + 1))
    if metric == "records":
        values = [annual.get(year, 0) for year in years]
    else:
        values = [annual.get(year) for year in years]
    title_suffix = f" · {disaster_type}" if disaster_type else " · Todos los desastres"
    fig, ax = _figure(f"Evolución en {country}{title_suffix}", "Año", METRICS[metric]["label"], (10.5, 4.6))
    ax.plot(years, values, color=PALETTE[0], linewidth=2.5, marker="o" if len(years) <= 35 else None, markersize=3.4)
    _format_axis(ax, metric)
    ax.margins(x=.015)
    return _png(fig)


def create_country_type_bar_graph(data, country, metric="records", start=1900, end=2025, disaster_type=""):
    metric = metric if metric in METRICS else "records"
    rows = [r for r in _filter_years(data, start, end) if r.get("Country", "").strip() == country]
    if disaster_type:
        rows = [r for r in rows if r.get("Disaster Type", "").strip() == disaster_type]
    totals = defaultdict(float)
    for row in rows:
        name = row.get("Disaster Type", "Sin especificar")
        value = _metric_value(row, metric)
        if value is not None:
            totals[name] += value
    ordered = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    fig, ax = _figure(f"{METRICS[metric]['label']} por tipo de desastre · {country}", METRICS[metric]["label"], "Tipo de desastre", (10, 5.2))
    if ordered:
        names, values = zip(*ordered)
        labels = list(names)[::-1]
        plot_values = list(values)[::-1]
        positions = list(range(len(labels)))
        bars = ax.barh(positions, plot_values, color=PALETTE[:len(values)][::-1], height=.68)
        ax.set_yticks(positions, labels=labels)
        ax.bar_label(bars, labels=[f"{v:,.0f}".replace(",", ".") for v in plot_values], padding=5, color=TEXT, fontsize=8)
        ax.margins(x=.14)
        _format_bar_axis(ax, metric)
    else:
        ax.text(.5, .5, "No hay datos para esta selección", color=MUTED, ha="center", va="center", transform=ax.transAxes)
    return _png(fig)


def create_disaster_ranking_graph(data, metric="records", start=1900, end=2025):
    """Rank disaster types by frequency or reported human impact."""
    metric = metric if metric in METRICS else "records"
    totals = defaultdict(float)
    for row in _filter_years(data, start, end):
        name = row.get("Disaster Type", "").strip()
        value = _metric_value(row, metric)
        if name and value is not None:
            totals[name] += value
    ordered = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    fig, ax = _figure(
        f"Tipos de desastre por {METRICS[metric]['short']}",
        METRICS[metric]["label"], "Tipo de desastre", (10.5, 5.4)
    )
    if ordered:
        names, values = zip(*ordered)
        labels = list(names)[::-1]
        plot_values = list(values)[::-1]
        positions = list(range(len(labels)))
        bars = ax.barh(positions, plot_values, color=PALETTE[0], height=.66)
        ax.set_yticks(positions, labels=labels)
        ax.bar_label(bars, labels=[f"{v:,.0f}".replace(",", ".") for v in plot_values],
                     padding=5, color=TEXT, fontsize=8)
        ax.margins(x=.14)
        _format_bar_axis(ax, metric)
    else:
        ax.text(.5, .5, "No hay datos para este periodo", color=MUTED, ha="center", va="center", transform=ax.transAxes)
    return _png(fig)


def create_geo_ranking_graph(data, metric="records", level="region", start=1900, end=2025):
    metric = metric if metric in METRICS else "records"
    key = "Region" if level == "region" else "Country"
    totals = defaultdict(float)
    for row in _filter_years(data, start, end):
        name = row.get(key, "").strip()
        value = _metric_value(row, metric)
        if name and value is not None:
            totals[name] += value
    ordered = sorted(totals.items(), key=lambda item: item[1], reverse=True)[:10]
    title = "Regiones" if level == "region" else "Países"
    fig, ax = _figure(f"Distribución de {METRICS[metric]['short']} por {title.lower()}", METRICS[metric]["label"], title, (10, 5.1))
    if ordered:
        names, values = zip(*ordered)
        labels = list(names)[::-1]
        plot_values = list(values)[::-1]
        positions = list(range(len(labels)))
        bars = ax.barh(positions, plot_values, color=PALETTE[0], height=.68)
        ax.set_yticks(positions, labels=labels)
        ax.bar_label(bars, labels=[f"{v:,.0f}".replace(",", ".") for v in plot_values],
                     padding=5, color=TEXT, fontsize=8)
        ax.margins(x=.14)
        _format_bar_axis(ax, metric)
    else:
        ax.text(.5, .5, "No hay datos para este periodo", color=MUTED, ha="center", va="center", transform=ax.transAxes)
    return _png(fig)


# Backwards-compatible wrappers for the original routes.
def create_time_graph(data, start=1900, end=2025, disaster_type="", metric="records"):
    selected = [disaster_type] if disaster_type else []
    return create_multi_series_graph(data, selected, "type", metric, start, end)


def create_type_graph(data, metric="records", start=1900, end=2025, selected_types=None):
    return create_multi_series_graph(data, selected_types or [], "type", metric, start, end)


def create_geo_graph(data, metric="records", level="region"):
    return create_geo_ranking_graph(data, metric, level)


def create_country_graph(data, country, metric="records"):
    return create_country_detail_graph(data, country, metric)


def create_country_types_graph(data, country):
    return create_country_type_bar_graph(data, country)
