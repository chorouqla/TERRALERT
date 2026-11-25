
const globeContainer = document.getElementById("globe-container");
const countrySelect = document.getElementById("country-select");

const placeholder = document.getElementById("country-placeholder");
const results = document.getElementById("country-results");

const numberFormat = new Intl.NumberFormat("es-ES");

let selectedCountry = null;

// Translate disaster categories into Spanish
const disasterTranslations = {
    "Flood": "Inundación",
    "Storm": "Tormenta",
    "Earthquake": "Terremoto",
    "Drought": "Sequía",
    "Wildfire": "Incendio forestal",
    "Volcanic activity": "Actividad volcánica",
    "Landslide": "Deslizamiento de tierra",
    "Extreme temperature": "Temperatura extrema",
    "Epidemic": "Epidemia",
    "Mass movement (dry)": "Movimiento en masa seco"
};

function translateType(type) {
    return disasterTranslations[type] || type;
}

// Load the country list from Flask
async function loadCountries() {
    const response = await fetch("/api/countries");
    const countries = await response.json();

    countrySelect.innerHTML = '<option value="">Selecciona un país</option>';

    countries.forEach(country => {
        const option = document.createElement("option");
        option.value = country.iso;
        option.textContent = country.name;
        countrySelect.appendChild(option);
    });
}

// Render the latest records below the globe. A selected country narrows this list.
async function loadLatestEvents(iso = "") {
    const container = document.getElementById("latest-events");
    const heading = document.getElementById("latest-title");
    if (!container) return;
    try {
        const response = await fetch(`/api/latest-events${iso ? `?iso=${encodeURIComponent(iso)}` : ""}`);
        if (!response.ok) throw new Error("No se pudieron cargar los eventos");
        const events = await response.json();
        heading.textContent = iso ? "Últimos eventos del país seleccionado" : "Últimos eventos registrados";
        container.innerHTML = events.map(event => `
            <a class="latest-event-card" href="/eventos?id=${encodeURIComponent(event.id)}">
                <span class="event-year">${event.year} · ${escapeText(event.region)}</span>
                <strong>${escapeText(translateType(event.type))}</strong>
                <span>${escapeText(event.country)} · ${numberFormat.format(event.deaths)} fallecidos registrados</span>
            </a>
        `).join("") || '<p class="events-message">No hay eventos disponibles.</p>';
    } catch (error) {
        console.error(error);
        container.innerHTML = '<p class="events-message">No se pudieron cargar los eventos recientes.</p>';
    }
}

function escapeText(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => ({
        "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#039;"
    })[character]);
}

// Display country information
async function selectCountry(iso) {
    if (!iso) return;

    const response = await fetch(`/api/country/${iso}`);

    if (!response.ok) {
        results.hidden = true;
        placeholder.hidden = false;

        placeholder.innerHTML = `
        <div class="placeholder-icon">ⓘ</div>
        <h3>Datos no disponibles</h3>
        <p>
            No hay registros de desastres asociados a esta región
            en la base de datos EM-DAT.
        </p>
    `;
        return;
    }

    const data = await response.json();

    selectedCountry = iso;
    countrySelect.value = iso;
    loadLatestEvents(iso);

    placeholder.hidden = true;
    results.hidden = false;

    document.getElementById("country-name").textContent = data.name;
    document.getElementById("country-iso").textContent = data.iso;

    document.getElementById("country-total").textContent =
        numberFormat.format(data.total);

    document.getElementById("country-deaths").textContent =
        numberFormat.format(data.deaths);

    document.getElementById("country-affected").textContent =
        numberFormat.format(data.affected);

    document.getElementById("country-main-type").textContent =
        translateType(data.main_type);

}

// Create the 3D Earth
async function createGlobe() {

    const globe = Globe()(globeContainer)
        .globeImageUrl(
            "https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
        )
        .backgroundImageUrl(
            "https://unpkg.com/three-globe/example/img/night-sky.png"
        )
        .showAtmosphere(true)
        .atmosphereColor("#42bfff")
        .atmosphereAltitude(0.18)
        .polygonAltitude(0.008)
        .polygonCapColor(() => "rgba(30, 130, 190, 0.12)")
        .polygonSideColor(() => "rgba(30, 130, 190, 0.08)")
        .polygonStrokeColor(() => "#47baff")
        .polygonLabel(feature => {
            const name = feature.properties.ADMIN || "País";
            return `<b>${name}</b><br>Haz clic para explorar`;
        })
        .onPolygonClick(feature => {
            const iso =
                feature.properties.ISO_A3_EH ||
                feature.properties.ADM0_A3 ||
                feature.properties.GU_A3;

            if (iso && iso !== "-99") {
                selectCountry(iso);
            }
        });

    globe.width(globeContainer.clientWidth);
    globe.height(globeContainer.clientHeight);

    // Starting view
    globe.pointOfView({
        lat: 20,
        lng: 0,
        altitude: 2.2
    }, 1000);

    // Load country borders
    const response = await fetch(
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson"
    );

    if (!response.ok) {
        throw new Error("No se pudieron cargar los países.");
    }

    const countries = await response.json();

    globe.polygonsData(countries.features);

    document.getElementById("globe-loading").remove();

    // Adapt the globe to the screen size
    window.addEventListener("resize", () => {
        globe.width(globeContainer.clientWidth);
        globe.height(globeContainer.clientHeight);
    });

    // Slowly rotate the Earth
    globe.controls().autoRotate = true;
    globe.controls().autoRotateSpeed = 0.35;

    return globe;
}

// Country selector interaction
countrySelect.addEventListener("change", () => {
    selectCountry(countrySelect.value);
});

// Start the dashboard
async function startDashboard() {
    try {
        await loadCountries();
        await createGlobe();
        await loadLatestEvents();
    } catch (error) {
        console.error(error);
        document.getElementById("globe-loading").textContent =
            "No se pudo cargar el globo. Comprueba tu conexión a Internet.";
    }
}

startDashboard();
