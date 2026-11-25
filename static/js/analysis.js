const $ = id => document.getElementById(id);
const MAX_TYPES = 5;
const MAX_COUNTRIES = 8;

function setImage(id, url) {
    const image = $(id);
    image.onerror = () => { image.alt = "No se pudo generar el gráfico. Comprueba los filtros e inténtalo de nuevo."; image.classList.add("chart-error"); };
    image.onload = () => image.classList.remove("chart-error");
    image.src = `${url}${url.includes("?") ? "&" : "?"}_=${Date.now()}`;
    image.hidden = false;
    if (id === "geo-series-chart") $("geo-series-placeholder").hidden = true;
}

function periodParams(prefix) {
    let start = Number($(prefix + "-start").value || 1900);
    let end = Number($(prefix + "-end").value || 2025);
    start = Math.max(1900, Math.min(2025, start));
    end = Math.max(1900, Math.min(2025, end));
    if (start > end) [start, end] = [end, start];
    $(prefix + "-start").value = start;
    $(prefix + "-end").value = end;
    return { start, end };
}

function fillSelect(id, values, placeholder = null) {
    const select = $(id);
    select.innerHTML = "";
    if (placeholder !== null) {
        const option = document.createElement("option"); option.value = ""; option.textContent = placeholder; select.appendChild(option);
    }
    values.forEach(value => { const option = document.createElement("option"); option.value = value; option.textContent = value; select.appendChild(option); });
}

function selectedValues(id) { return [...$(id).options].filter(option => option.selected).map(option => option.value); }

function buildParams(prefix, metricId) {
    const period = periodParams(prefix);
    return new URLSearchParams({ start: period.start, end: period.end, metric: $(metricId).value });
}

function setupTypeChoices(types, topTypes) {
    const host = $("time-type-options");
    const chosen = new Set();
    host.innerHTML = "";
    types.forEach((type, index) => {
        const label = document.createElement("label"); label.className = "choice-pill";
        const input = document.createElement("input"); input.type = "checkbox"; input.value = type;
        input.addEventListener("change", () => {
            if (input.checked && chosen.size >= MAX_TYPES) { input.checked = false; return; }
            input.checked ? chosen.add(type) : chosen.delete(type);
            updateCount();
        });
        const text = document.createElement("span"); text.textContent = type;
        label.append(input, text); host.appendChild(label);
    });
    function updateCount() { $("time-selection-count").textContent = chosen.size ? `${chosen.size} de ${MAX_TYPES} tipos seleccionados` : "Se mostrarán los 5 tipos principales"; }
    function selectTop() {
        [...host.querySelectorAll("input")].forEach(input => {
            input.checked = topTypes.includes(input.value);
            if (input.checked) chosen.add(input.value);
        });
        updateCount();
    }
    $("time-select-top").addEventListener("click", () => { chosen.clear(); [...host.querySelectorAll("input")].forEach(input => { input.checked = false; }); selectTop(); });
    $("time-clear-types").addEventListener("click", () => { chosen.clear(); [...host.querySelectorAll("input")].forEach(input => { input.checked = false; }); updateCount(); });
    selectTop();
    return () => [...chosen];
}

function setupCountryPicker(countries) {
    const search = $("geo-country-search"), datalist = $("geo-country-suggestions"), hidden = $("geo-countries"), chips = $("geo-selected-countries");
    countries.forEach(country => { const item = document.createElement("option"); item.value = country; datalist.appendChild(item); const option = document.createElement("option"); option.value = country; option.textContent = country; hidden.appendChild(option); });
    function chosen() { return selectedValues("geo-countries"); }
    function render() {
        chips.innerHTML = "";
        const values = chosen();
        if (!values.length) { chips.innerHTML = '<span class="picker-hint">Añade entre 2 y 8 países para comparar</span>'; }
        values.forEach(country => {
            const chip = document.createElement("span"); chip.className = "country-chip";
            const name = document.createElement("span"); name.textContent = country;
            const remove = document.createElement("button"); remove.type = "button"; remove.textContent = "×"; remove.setAttribute("aria-label", `Quitar ${country}`);
            remove.addEventListener("click", () => { const opt = [...hidden.options].find(o => o.value === country); if (opt) opt.selected = false; render(); });
            chip.append(name, remove); chips.appendChild(chip);
        });
        $("geo-selection-count").textContent = values.length ? `${values.length} país${values.length === 1 ? "" : "es"} seleccionado${values.length === 1 ? "" : "s"}` : "Sin países seleccionados";
    }
    function add(value) {
        const match = [...hidden.options].find(option => option.value.toLocaleLowerCase() === value.trim().toLocaleLowerCase());
        if (!match || match.selected || chosen().length >= MAX_COUNTRIES) return false;
        match.selected = true; render(); return true;
    }
    search.addEventListener("change", () => { add(search.value); search.value = ""; });
    search.addEventListener("keydown", event => { if (event.key === "Enter") { event.preventDefault(); if (add(search.value)) search.value = ""; } });
    $("clear-countries").addEventListener("click", () => { [...hidden.options].forEach(option => option.selected = false); render(); });
    render(); return chosen;
}

async function updateInsight(targetId, params, scope, extras = {}) {
    const query = new URLSearchParams(params);
    query.set("scope", scope);
    Object.entries(extras).forEach(([key, value]) => {
        if (Array.isArray(value)) value.forEach(item => query.append(key, item));
        else if (value !== undefined && value !== null && value !== "") query.set(key, value);
    });
    const target = $(targetId);
    try {
        const response = await fetch("/api/analysis/insight?" + query);
        const data = await response.json();
        target.textContent = data.insight || "No hay una interpretación disponible.";
    } catch (error) {
        target.textContent = "No se pudo generar la interpretación de estos datos.";
    }
}

async function initAnalysis() {
    const response = await fetch("/api/analysis/options");
    if (!response.ok) throw new Error("No se pudieron cargar las opciones.");
    const options = await response.json();
    fillSelect("country-type", options.types, "Todos los tipos");
    fillSelect("country-analysis", options.countries, "Selecciona un país");
    const getTypes = setupTypeChoices(options.types, options.top_types || options.types.slice(0, MAX_TYPES));
    const getCountries = setupCountryPicker(options.countries);

    function updateTime() {
        const params = buildParams("time", "time-metric");
        const types = getTypes();
        if (types.length) types.forEach(type => params.append("item", type));
        else params.set("default_limit", "5");
        setImage("time-chart", "/api/analysis/series.png?group=type&" + params);
        updateInsight("time-insight", params, "series", {group: "type"});
    }
    $("update-time").addEventListener("click", updateTime);

    $("update-disaster-ranking").addEventListener("click", () => {
        const params = buildParams("disaster-rank", "disaster-ranking-metric");
        setImage("disaster-ranking-chart", "/api/analysis/disaster-ranking.png?" + params);
        updateInsight("disaster-ranking-insight", params, "ranking", {level: "type"});
    });

    $("update-ranking").addEventListener("click", () => {
        const params = buildParams("rank", "geo-ranking-metric"); params.set("level", $("geo-level").value);
        setImage("geo-ranking-chart", "/api/analysis/ranking.png?" + params);
        updateInsight("geo-ranking-insight", params, "ranking", {level: $("geo-level").value});
    });

    $("update-geo-series").addEventListener("click", () => {
        const countries = getCountries();
        if (!countries.length) { $("geo-selection-count").textContent = "Añade al menos un país para generar la comparación"; return; }
        const params = buildParams("geo", "geo-metric"); countries.forEach(country => params.append("item", country));
        setImage("geo-series-chart", "/api/analysis/series.png?group=country&" + params);
        updateInsight("geo-series-insight", params, "series", {group: "country"});
    });

    function updateCountry() {
        const country = $("country-analysis").value;
        if (!country) { $("country-summary").textContent = "Selecciona un país para comenzar."; $("country-chart").hidden = true; $("country-types-chart").hidden = true; return; }
        const params = buildParams("country", "country-metric"); params.set("country", country);
        const type = $("country-type").value; if (type) params.set("type", type);
        setImage("country-chart", "/api/analysis/country-detail.png?" + params);
        setImage("country-types-chart", "/api/analysis/country-breakdown.png?" + params);
        const metric = $("country-metric").selectedOptions[0].textContent;
        $("country-summary").textContent = `${country} · ${params.get("start")}–${params.get("end")} · ${metric}${type ? " · " + type : " · Todos los tipos"}`;
        updateInsight("country-insight", params, "country", {country, type});
    }
    $("update-country").addEventListener("click", updateCountry);
    ["country-analysis", "country-type", "country-start", "country-end", "country-metric"].forEach(id => $(id).addEventListener("change", updateCountry));

    updateTime();
    $("update-disaster-ranking").click();
    $("update-ranking").click();
}

initAnalysis().catch(error => {
    console.error("Error al inicializar análisis:", error);
    const summary = $("country-summary"); if (summary) summary.textContent = "No se pudieron cargar los filtros. Comprueba el servidor y recarga la página.";
});
