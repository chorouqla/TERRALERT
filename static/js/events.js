
const searchInput = document.getElementById("event-search");
const yearFromInput = document.getElementById("year-from");
const yearToInput = document.getElementById("year-to");
const typeSelect = document.getElementById("disaster-type");
const sort1Select = document.getElementById("sort1");
const regionSelect = document.getElementById("region-filter");
const countrySelect = document.getElementById("country-filter");
const orderSelect = document.getElementById("sort-order");

const applyButton = document.getElementById("apply-filters");
const resetButton = document.getElementById("reset-filters");

const tableBody = document.getElementById("events-table-body");
const resultsCount = document.getElementById("results-count");
const loadingMessage = document.getElementById("events-loading");
const errorMessage = document.getElementById("events-error");
const emptyMessage = document.getElementById("events-empty");
const pagination = document.getElementById("pagination");
const paginationInfo = document.getElementById("pagination-info");

let currentPage = 1;


// Translate disaster categories into Spanish
const disasterTranslations = {
    "Flood": "Inundación",
    "Storm": "Tormenta",
    "Earthquake": "Terremoto",
    "Drought": "Sequía",
    "Volcanic activity": "Actividad volcánica",
    "Landslide": "Deslizamiento de tierra",
    "Wildfire": "Incendio forestal",
    "Extreme temperature": "Temperatura extrema",
    "Mass movement (dry)": "Movimiento en masa (seco)"
};


function translateType(type) {
    return disasterTranslations[type] || type || "No disponible";
}


function formatNumber(value) {
    return new Intl.NumberFormat("es-ES").format(value || 0);
}


function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, character => {
        const characters = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        };

        return characters[character];
    });
}


// Load the available disaster categories
async function loadDisasterTypes() {
    try {
        const response = await fetch("/api/events");

        if (!response.ok) {
            throw new Error("No se pudieron cargar los tipos");
        }

        const data = await response.json();

        data.types.forEach(type => {
            const option = document.createElement("option");

            option.value = type;
            option.textContent = translateType(type);

            typeSelect.appendChild(option);
        });

    } catch (error) {
        console.error(error);
    }
}


// Load geographic filters from the actual EM-DAT dataset.
async function loadGeographyFilters() {
    const response = await fetch("/api/geography");
    if (!response.ok) throw new Error("No se pudieron cargar las regiones");
    const data = await response.json();
    data.regions.forEach(region => {
        const option = document.createElement("option");
        option.value = region;
        option.textContent = region;
        regionSelect.appendChild(option);
    });
    function updateCountries() {
        const previous = countrySelect.value;
        const available = regionSelect.value
            ? (data.countries_by_region[regionSelect.value] || [])
            : Object.values(data.countries_by_region).flat();
        countrySelect.innerHTML = '<option value="">Todos los países</option>';
        [...new Set(available)].sort().forEach(country => {
            const option = document.createElement("option");
            option.value = country;
            option.textContent = country;
            countrySelect.appendChild(option);
        });
        countrySelect.value = available.includes(previous) ? previous : "";
    }
    regionSelect.addEventListener("change", () => { updateCountries(); loadEvents(1); });
    countrySelect.addEventListener("change", () => loadEvents(1));
    updateCountries();
}

// Get the selected filters and send them to Flask
async function loadEvents(page = 1) {
    currentPage = page;

    loadingMessage.hidden = false;
    errorMessage.hidden = true;
    emptyMessage.hidden = true;

    tableBody.innerHTML = "";
    pagination.innerHTML = "";

    const parameters = new URLSearchParams({
        search: searchInput.value,
        year_from: yearFromInput.value || 1900,
        year_to: yearToInput.value || 2025,
        type: typeSelect.value,
        sort1: sort1Select.value,
        region: regionSelect.value,
        country: countrySelect.value,
        order: orderSelect.value,
        page: currentPage
    });

    try {
        const response = await fetch(`/api/events?${parameters}`);

        if (!response.ok) {
            throw new Error("Error al cargar los eventos");
        }

        const data = await response.json();

        loadingMessage.hidden = true;

        resultsCount.textContent =
            `${formatNumber(data.total)} resultados`;

        paginationInfo.textContent =
            `Mostrando ${formatNumber(data.start)}–${formatNumber(data.end)} de ${formatNumber(data.total)} registros`;

        if (data.events.length === 0) {
            emptyMessage.hidden = false;
            return;
        }

        displayEvents(data.events);
        displayPagination(data.page, data.total_pages);
        const targetId = new URLSearchParams(window.location.search).get("id");
        if (targetId) {
            const row = [...tableBody.querySelectorAll("tr.event-row")].find(tr => tr.dataset.eventId === targetId);
            if (row) {
                row.classList.add("event-highlight");
                if (row.nextElementSibling) row.nextElementSibling.hidden = false;
                row.scrollIntoView({ behavior: "smooth", block: "center" });
            }
        }

    } catch (error) {
        console.error(error);

        loadingMessage.hidden = true;
        errorMessage.hidden = false;

        resultsCount.textContent = "Error";
        paginationInfo.textContent = "";
    }
}


// Display the event rows
function displayEvents(events) {
    tableBody.innerHTML = events.map((event, index) => `
        <tr class="event-row" data-event-id="${escapeHTML(event.id)}">
            <td>${escapeHTML(event.year)}</td>
            <td class="event-country">${escapeHTML(event.country)}</td>
            <td>${escapeHTML(translateType(event.type))}</td>
            <td>${formatNumber(event.deaths)}</td>
            <td>${formatNumber(event.affected)}</td>
            <td>
                <button
                    type="button"
                    class="details-button"
                    data-event-index="${index}">
                    Ver detalles
                </button>
            </td>
        </tr>

        <tr class="event-details-row" id="details-${index}" hidden>
            <td colspan="6">
                <div class="event-details-content">

                    <div>
                        <span>Subtipo</span>
                        <strong>${escapeHTML(translateType(event.subtype) || "No disponible")}</strong>
                    </div>

                    <div>
                        <span>Ubicación</span>
                        <strong>${escapeHTML(event.location || "No disponible")}</strong>
                    </div>

                    <div>
                        <span>Heridos</span>
                        <strong>${formatNumber(event.injured)}</strong>
                    </div>

                    <div>
                        <span>Personas sin hogar</span>
                        <strong>${formatNumber(event.homeless)}</strong>
                    </div>

                    <div>
                        <span>Daños económicos (miles de US$)</span>
                        <strong>${event.damage === null ? "No disponible" : formatNumber(event.damage)}</strong>
                    </div>

                    <div>
                        <span>Magnitud</span>
                        <strong>${escapeHTML(event.magnitude || "No disponible")}</strong>
                    </div>

                    <div>
                        <span>Escala de magnitud</span>
                        <strong>${escapeHTML(event.magnitude_scale || "No disponible")}</strong>
                    </div>

                    <div>
                        <span>Origen</span>
                        <strong>${escapeHTML(event.origin || "No disponible")}</strong>
                    </div>

                    <div>
                        <span>Identificador EM-DAT</span>
                        <strong>${escapeHTML(event.id || "No disponible")}</strong>
                    </div>

                </div>
            </td>
        </tr>
    `).join("");
}


// Open and close the details of an event
tableBody.addEventListener("click", function (event) {
    const button = event.target.closest(".details-button");

    if (!button) return;

    const index = button.dataset.eventIndex;
    const detailsRow = document.getElementById(`details-${index}`);

    detailsRow.hidden = !detailsRow.hidden;

    button.textContent = detailsRow.hidden
        ? "Ver detalles"
        : "Ocultar detalles";
});


// Create the page buttons
function displayPagination(page, totalPages) {
    pagination.innerHTML = "";

    if (totalPages <= 1) return;

    const previousButton = document.createElement("button");
    previousButton.textContent = "← Anterior";
    previousButton.disabled = page === 1;

    previousButton.addEventListener("click", () => {
        loadEvents(page - 1);
    });

    pagination.appendChild(previousButton);

    for (let number = 1; number <= totalPages; number++) {
        if (
            number === 1 ||
            number === totalPages ||
            Math.abs(number - page) <= 1
        ) {
            const pageButton = document.createElement("button");

            pageButton.textContent = number;

            if (number === page) {
                pageButton.classList.add("active");
            }

            pageButton.addEventListener("click", () => {
                loadEvents(number);
            });

            pagination.appendChild(pageButton);

        } else if (
            number === page - 2 ||
            number === page + 2
        ) {
            const dots = document.createElement("span");
            dots.textContent = "...";

            pagination.appendChild(dots);
        }
    }

    const nextButton = document.createElement("button");
    nextButton.textContent = "Siguiente →";
    nextButton.disabled = page === totalPages;

    nextButton.addEventListener("click", () => {
        loadEvents(page + 1);
    });

    pagination.appendChild(nextButton);
}


// Apply filters
applyButton.addEventListener("click", () => {
    loadEvents(1);
});


// Press Enter to search
searchInput.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        loadEvents(1);
    }
});


// Reset all filters
resetButton.addEventListener("click", () => {
    searchInput.value = "";
    yearFromInput.value = 1900;
    yearToInput.value = 2025;
    typeSelect.value = "";
    sort1Select.value = "year";
    regionSelect.value = "";
    countrySelect.innerHTML = '<option value="">Todos los países</option>';
    fetch("/api/geography").then(response => response.json()).then(data => {
        Object.values(data.countries_by_region).flat().filter((value, index, array) => array.indexOf(value) === index).sort().forEach(country => {
            const option = document.createElement("option");
            option.value = country;
            option.textContent = country;
            countrySelect.appendChild(option);
        });
    });
    orderSelect.value = "desc";

    loadEvents(1);
});


// Initial page loading
Promise.all([loadDisasterTypes(), loadGeographyFilters()]).then(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.has("id")) searchInput.value = params.get("id");
    loadEvents(1);
}).catch(error => {
    console.error(error);
    loadEvents(1);
});
