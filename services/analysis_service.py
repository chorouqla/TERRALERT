from collections import defaultdict

METRIC_COLUMNS = {
    "records": None,
    "deaths": "Total Deaths",
    "affected": "Total Affected",
}
METRIC_LABELS = {
    "records": "registros",
    "deaths": "fallecimientos reportados",
    "affected": "personas afectadas reportadas",
}


def _value(row, metric):
    column = METRIC_COLUMNS.get(metric)
    if column is None:
        return 1.0
    raw = row.get(column)
    if raw is None or str(raw).strip().lower() in ("", "nan", "none"):
        return None
    try:
        return float(str(raw).strip().replace(" ", "").replace(",", "."))
    except (TypeError, ValueError):
        return None


def _fmt(value):
    return f"{value:,.0f}".replace(",", ".")


def build_insight(data, scope="series", metric="records", start=1900, end=2025,
                  group="type", selected=None, level="region", country="", disaster_type=""):
    metric = metric if metric in METRIC_COLUMNS else "records"
    rows = [row for row in data if start <= row.get("year", 0) <= end]
    label = METRIC_LABELS[metric]

    if scope == "country":
        rows = [row for row in rows if row.get("Country", "").strip() == country]
        if disaster_type:
            rows = [row for row in rows if row.get("Disaster Type", "").strip() == disaster_type]
        valid = sum(_value(row, metric) is not None for row in rows)
        if not rows:
            return "No se encontraron registros para esta combinación de filtros."
        if metric == "records":
            return f"Se encontraron {_fmt(len(rows))} registros de {country} entre {start} y {end}."
        return (f"{country}: {_fmt(valid)} de {_fmt(len(rows))} registros contienen datos de "
                f"{label}. Los registros restantes no se interpretan como impacto cero.")

    if scope == "series":
        column = "Disaster Type" if group == "type" else "Country"
        selected = selected or []
        if not selected and group == "type":
            defaults = defaultdict(float)
            for row in rows:
                name = row.get(column, "").strip()
                value = _value(row, metric)
                if name and value is not None:
                    defaults[name] += value
            selected = [name for name, _ in sorted(defaults.items(), key=lambda item: item[1], reverse=True)[:5]]
        if selected:
            rows = [row for row in rows if row.get(column, "").strip() in selected]
        totals = defaultdict(float)
        for row in rows:
            value = _value(row, metric)
            name = row.get(column, "").strip()
            if name and value is not None:
                totals[name] += value
        if not totals:
            return "No hay datos suficientes para esta selección y este indicador."
        leader, total = max(totals.items(), key=lambda item: item[1])
        unit = "registros" if metric == "records" else label
        coverage = sum(_value(row, metric) is not None for row in rows)
        coverage_note = "" if metric == "records" else f" Cobertura: {_fmt(coverage)} de {_fmt(len(rows))} registros seleccionados."
        return f"Entre {start} y {end}, {leader} concentra el mayor total de {unit} dentro de la selección ({_fmt(total)}).{coverage_note}"

    if scope == "ranking":
        column = "Disaster Type" if level == "type" else ("Region" if level == "region" else "Country")
        totals = defaultdict(float)
        for row in rows:
            value = _value(row, metric)
            name = row.get(column, "").strip()
            if name and value is not None:
                totals[name] += value
        if not totals:
            return "No hay datos suficientes para calcular este ranking."
        leader, total = max(totals.items(), key=lambda item: item[1])
        noun = {"Disaster Type": "tipos de desastre", "Region": "regiones", "Country": "países"}[column]
        coverage = sum(_value(row, metric) is not None for row in rows)
        note = "" if metric == "records" else f" Se dispone de datos del indicador en {_fmt(coverage)} de {_fmt(len(rows))} registros del periodo."
        return f"{leader} presenta el mayor total de {label} entre los {noun} comparados ({_fmt(total)}) durante {start}–{end}.{note}"

    return "Selecciona filtros para explorar los datos."
