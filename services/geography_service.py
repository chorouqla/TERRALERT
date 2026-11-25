
def get_geography_options(data):
    regions = sorted({r.get("Region", "").strip() for r in data if r.get("Region", "").strip()})
    countries_by_region = {}
    for row in data:
        region = row.get("Region", "").strip()
        country = row.get("Country", "").strip()
        if region and country:
            countries_by_region.setdefault(region, set()).add(country)
    return {
        "regions": regions,
        "countries_by_region": {
            region: sorted(countries) for region, countries in countries_by_region.items()
        }
    }
