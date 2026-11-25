from flask import Flask, render_template, jsonify, request, send_file
from services.data_service import (
    load_data, get_countries, get_global_stats, get_country_stats,
    get_filtered_events, get_latest_events
)
from services.geography_service import get_geography_options
from services.analysis_service import build_insight
from services.graph_service import (
    create_time_graph, create_type_graph, create_geo_graph, create_country_graph, create_country_types_graph,
    create_multi_series_graph, create_country_detail_graph,
    create_country_type_bar_graph, create_geo_ranking_graph,
    create_disaster_ranking_graph
)

app = Flask(__name__)

@app.route("/")
def dashboard():
    data = load_data()
    return render_template("dashboard.html", stats=get_global_stats(data))

@app.route("/analisis")
def analysis():
    data = load_data()
    return render_template("analysis.html", stats=get_global_stats(data))

@app.route("/eventos")
def events():
    return render_template("events.html")

@app.route("/api/countries")
def countries():
    return jsonify(get_countries(load_data()))

@app.route("/api/country/<iso>")
def country(iso):
    data = load_data()
    result = get_country_stats(data, iso.upper())
    if result is None:
        return jsonify({"error": "País no encontrado"}), 404
    return jsonify(result)

@app.route("/api/latest-events")
def latest_events():
    iso = request.args.get("iso", "").strip() or None
    return jsonify(get_latest_events(load_data(), iso=iso, limit=6))

@app.route("/api/geography")
def geography():
    return jsonify(get_geography_options(load_data()))

@app.route("/api/analysis/options")
def analysis_options():
    data = load_data()
    type_counts = {}
    for row in data:
        disaster_type = row.get("Disaster Type", "").strip()
        if disaster_type:
            type_counts[disaster_type] = type_counts.get(disaster_type, 0) + 1
    return jsonify({
        "types": sorted(type_counts),
        "top_types": [name for name, _ in sorted(type_counts.items(), key=lambda item: item[1], reverse=True)[:5]],
        "countries": sorted({r.get("Country", "") for r in data if r.get("Country")}),
        "regions": sorted({r.get("Region", "") for r in data if r.get("Region")}),
        "min_year": min(r["year"] for r in data),
        "max_year": max(r["year"] for r in data)
    })


def _analysis_period():
    try:
        start = int(request.args.get("start", 1900))
        end = int(request.args.get("end", 2025))
    except (TypeError, ValueError):
        start, end = 1900, 2025
    start = max(1900, min(start, 2025))
    end = max(1900, min(end, 2025))
    return (end, start) if start > end else (start, end)


@app.route("/api/analysis/insight")
def analysis_insight():
    try:
        start, end = _analysis_period()
        selected = request.args.getlist("item")
        insight = build_insight(
            load_data(), scope=request.args.get("scope", "series"),
            metric=request.args.get("metric", "records"), start=start, end=end,
            group=request.args.get("group", "type"), selected=selected,
            level=request.args.get("level", "region"),
            country=request.args.get("country", ""),
            disaster_type=request.args.get("type", "")
        )
        return jsonify({"insight": insight})
    except Exception:
        app.logger.exception("No se pudo generar la interpretación del análisis")
        return jsonify({"insight": "No se pudo calcular una interpretación para estos filtros."}), 500


@app.route("/api/analysis/series.png")
def analysis_series_graph():
    group = request.args.get("group", "type")
    if group not in ("type", "country"):
        group = "type"
    metric = request.args.get("metric", "records")
    if metric not in ("records", "deaths", "affected"):
        metric = "records"
    start, end = _analysis_period()
    selected = request.args.getlist("item")
    scale = request.args.get("scale", "linear")
    if scale not in ("linear", "log"):
        scale = "linear"
    return send_file(
        create_multi_series_graph(load_data(), selected, group, metric, start, end, scale),
        mimetype="image/png"
    )


@app.route("/api/analysis/disaster-ranking.png")
def analysis_disaster_ranking_graph():
    metric = request.args.get("metric", "records")
    if metric not in ("records", "deaths", "affected"):
        metric = "records"
    start, end = _analysis_period()
    return send_file(create_disaster_ranking_graph(load_data(), metric, start, end), mimetype="image/png")


@app.route("/api/analysis/ranking.png")
def analysis_ranking_graph():
    metric = request.args.get("metric", "records")
    if metric not in ("records", "deaths", "affected"):
        metric = "records"
    level = request.args.get("level", "region")
    if level not in ("region", "country"):
        level = "region"
    start, end = _analysis_period()
    return send_file(create_geo_ranking_graph(load_data(), metric, level, start, end), mimetype="image/png")


@app.route("/api/analysis/country-detail.png")
def analysis_country_detail_graph():
    country_name = request.args.get("country", "")
    if not country_name:
        return jsonify({"error": "Selecciona un país"}), 400
    metric = request.args.get("metric", "records")
    if metric not in ("records", "deaths", "affected"):
        metric = "records"
    start, end = _analysis_period()
    disaster_type = request.args.get("type", "")
    return send_file(
        create_country_detail_graph(load_data(), country_name, metric, start, end, disaster_type),
        mimetype="image/png"
    )


@app.route("/api/analysis/country-breakdown.png")
def analysis_country_breakdown_graph():
    country_name = request.args.get("country", "")
    if not country_name:
        return jsonify({"error": "Selecciona un país"}), 400
    metric = request.args.get("metric", "records")
    if metric not in ("records", "deaths", "affected"):
        metric = "records"
    start, end = _analysis_period()
    disaster_type = request.args.get("type", "")
    return send_file(
        create_country_type_bar_graph(load_data(), country_name, metric, start, end, disaster_type),
        mimetype="image/png"
    )


@app.route("/api/analysis/time.png")
def analysis_time_graph():
    start, end = _analysis_period()
    disaster_type = request.args.get("type", "")
    metric = request.args.get("metric", "records")
    if metric not in ("records", "deaths", "affected"):
        metric = "records"
    return send_file(create_time_graph(load_data(), start, end, disaster_type, metric), mimetype="image/png")


@app.route("/api/analysis/types.png")
def analysis_types_graph():
    start, end = _analysis_period()
    selected = request.args.getlist("type")
    metric = request.args.get("metric", "records")
    if metric not in ("records", "deaths", "affected"):
        metric = "records"
    return send_file(create_type_graph(load_data(), metric, start, end, selected), mimetype="image/png")


@app.route("/api/analysis/geography.png")
def analysis_geography_graph():
    metric = request.args.get("metric", "records")
    if metric not in ("records", "deaths", "affected"):
        metric = "records"
    level = request.args.get("level", "region")
    if level not in ("region", "country"):
        level = "region"
    start, end = _analysis_period()
    return send_file(create_geo_ranking_graph(load_data(), metric, level, start, end), mimetype="image/png")


@app.route("/api/analysis/country.png")
def analysis_country_graph():
    country_name = request.args.get("country", "")
    if not country_name:
        return jsonify({"error": "Selecciona un país"}), 400
    start, end = _analysis_period()
    metric = request.args.get("metric", "records")
    if metric not in ("records", "deaths", "affected"):
        metric = "records"
    return send_file(create_country_detail_graph(load_data(), country_name, metric, start, end), mimetype="image/png")


@app.route("/api/analysis/country-types.png")
def analysis_country_types_graph():
    country_name = request.args.get("country", "")
    if not country_name:
        return jsonify({"error": "Selecciona un país"}), 400
    start, end = _analysis_period()
    metric = request.args.get("metric", "records")
    if metric not in ("records", "deaths", "affected"):
        metric = "records"
    return send_file(create_country_type_bar_graph(load_data(), country_name, metric, start, end), mimetype="image/png")

@app.route("/api/events")
def events_api():
    data = load_data()
    try:
        year_from = int(request.args.get("year_from", 1900))
        year_to = int(request.args.get("year_to", 2025))
        page = int(request.args.get("page", 1))
    except ValueError:
        return jsonify({"error": "Parámetros no válidos"}), 400
    if year_from > year_to:
        year_from, year_to = year_to, year_from
    result = get_filtered_events(
        data=data,
        search=request.args.get("search", ""),
        year_from=year_from,
        year_to=year_to,
        disaster_type=request.args.get("type", ""),
        sort1=request.args.get("sort1", "year"),
        sort2="",
        order=request.args.get("order", "desc"),
        page=page,
        region=request.args.get("region", ""),
        country=request.args.get("country", "")
    )
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)
