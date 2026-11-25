
import csv
import os
import math

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "data", "emdat_disasters.csv")


def number(value):
    """Convert a CSV value into a number safely."""
    try:
        if value is None or str(value).strip() == "":
            return 0

        return float(str(value).strip().replace(",", "."))

    except (ValueError, AttributeError):
        return 0


def load_data():
    """Load natural disasters from 1900 to 2025."""
    with open(CSV_PATH, mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        data = []

        for row in reader:
            year = int(number(row.get("Start Year")))

            if (
                row.get("Disaster Group") == "Natural"
                and 1900 <= year <= 2025
            ):
                row["year"] = year
                data.append(row)

    return data


def get_countries(data):
    """Return countries with their ISO codes."""
    countries = {}

    for row in data:
        iso = row.get("ISO", "").strip()
        country = row.get("Country", "").strip()

        if iso and country:
            countries[iso] = country

    return [
        {"iso": iso, "name": name}
        for iso, name in sorted(countries.items(), key=lambda x: x[1])
    ]


def get_global_stats(data):
    """Calculate the main global statistics."""
    return {
        "total": len(data),
        "deaths": int(sum(number(row.get("Total Deaths")) for row in data)),
        "affected": int(sum(number(row.get("Total Affected")) for row in data)),
        "countries": len(set(
            row.get("ISO") for row in data if row.get("ISO")
        )),
    }


def get_country_stats(data, iso):
    """Calculate statistics and recent events for one country."""
    country_data = [
        row for row in data
        if row.get("ISO", "").strip() == iso
    ]

    if not country_data:
        return None

    types = {}

    for row in country_data:
        disaster_type = row.get("Disaster Type", "Unknown")
        types[disaster_type] = types.get(disaster_type, 0) + 1

    events = sorted(
        country_data,
        key=lambda row: row["year"],
        reverse=True
    )

    return {
        "name": country_data[0].get("Country", ""),
        "iso": iso,
        "total": len(country_data),
        "deaths": int(sum(
            number(row.get("Total Deaths")) for row in country_data
        )),
        "affected": int(sum(
            number(row.get("Total Affected")) for row in country_data
        )),
        "main_type": max(types, key=types.get),
        "types": types,
        "events": [
            {
                "id": row.get("DisNo.", ""),
                "year": row["year"],
                "type": row.get("Disaster Type", ""),
                "subtype": row.get("Disaster Subtype", ""),
                "location": row.get("Location", ""),
                "deaths": int(number(row.get("Total Deaths"))),
                "affected": int(number(row.get("Total Affected"))),
            }
            for row in events[:10]
        ],
    }


def get_filtered_events(
    data,
    search="",
    year_from=1900,
    year_to=2025,
    disaster_type="",
    sort1="year",
    sort2="",
    order="desc",
    page=1,
    region="",
    country=""
):
    """Filter, sort and paginate disaster records."""

    # Available sorting columns
    sort_options = {
        "year": lambda row: row["year"],
        "country": lambda row: row.get("Country", "").lower(),
        "type": lambda row: row.get("Disaster Type", "").lower(),
        "deaths": lambda row: number(row.get("Total Deaths")),
        "affected": lambda row: number(row.get("Total Affected")),
    }

    # Validate sorting options
    if sort1 not in sort_options:
        sort1 = "year"

    if sort2 not in sort_options or sort2 == sort1:
        sort2 = ""

    reverse = order == "desc"

    # Filter by year
    filtered = [
        row for row in data
        if year_from <= row["year"] <= year_to
    ]


    if region:
        filtered = [row for row in filtered if row.get("Region", "").strip() == region]
    if country:
        filtered = [row for row in filtered if row.get("Country", "").strip() == country]

    # Filter by disaster type
    if disaster_type:
        filtered = [
            row for row in filtered
            if row.get("Disaster Type", "") == disaster_type
        ]

    # Search by country, type, subtype or location
    search = search.strip().lower()

    if search:
        filtered = [
            row for row in filtered
            if search in " ".join([
                row.get("Country", ""),
                row.get("Disaster Type", ""),
                row.get("Disaster Subtype", ""),
                row.get("Location", ""),
                row.get("DisNo.", ""),
            ]).lower()
        ]

    # Apply sorting
    if sort2:
        filtered.sort(key=sort_options[sort2], reverse=reverse)

    filtered.sort(key=sort_options[sort1], reverse=reverse)

    # Pagination
    page_size = 20
    total = len(filtered)
    total_pages = max(1, math.ceil(total / page_size))

    page = max(1, min(page, total_pages))

    start = (page - 1) * page_size
    page_data = filtered[start:start + page_size]

    # Prepare records for the browser
    events = []

    for row in page_data:
        events.append({
            "id": row.get("DisNo.", ""),
            "year": row["year"],
            "country": row.get("Country", ""),
            "type": row.get("Disaster Type", ""),
            "subtype": row.get("Disaster Subtype", ""),
            "location": row.get("Location", ""),
            "deaths": int(number(row.get("Total Deaths"))),
            "injured": int(number(row.get("No. Injured"))),
            "affected": int(number(row.get("Total Affected"))),
            "homeless": int(number(row.get("No. Homeless"))),
            "damage": number(row.get("Total Damage, Adjusted ('000 US$')")) if row.get("Total Damage, Adjusted ('000 US$')", "").strip() else None,
            "magnitude": row.get("Magnitude", ""),
            "magnitude_scale": row.get("Magnitude Scale", ""),
            "origin": row.get("Origin", ""),
        })

    # List of disaster types for the filter
    types = sorted(set(
        row.get("Disaster Type", "")
        for row in data
        if row.get("Disaster Type")
    ))

    return {
        "events": events,
        "types": types,
        "regions": sorted(set(row.get("Region", "").strip() for row in data if row.get("Region", "").strip())),
        "countries": sorted(set(row.get("Country", "").strip() for row in data if row.get("Country", "").strip())),
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "page_size": page_size,
        "start": start + 1 if total else 0,
        "end": min(start + page_size, total),
    }


def get_latest_events(data, iso=None, limit=6):
    """Return the latest records globally or for one ISO country code."""
    rows = data
    if iso:
        rows = [row for row in rows if row.get("ISO", "").strip() == iso]
    rows = sorted(rows, key=lambda row: (row["year"], row.get("DisNo.", "")), reverse=True)
    return [{
        "id": row.get("DisNo.", ""),
        "year": row["year"],
        "country": row.get("Country", ""),
        "type": row.get("Disaster Type", ""),
        "deaths": int(number(row.get("Total Deaths"))),
        "region": row.get("Region", "")
    } for row in rows[:limit]]
