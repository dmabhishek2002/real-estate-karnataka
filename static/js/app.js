/* ============================================================
   REAL ESTATE INTELLIGENCE
   MAIN APPLICATION JAVASCRIPT
   ============================================================ */


/* ============================================================
   GLOBAL STATE
   ============================================================ */

let compareList = [];

let allProperties = [];


/* ============================================================
   DOM READY
   ============================================================ */

document.addEventListener("DOMContentLoaded", () => {

    loadDistricts();

    setupEventListeners();

    createComparisonBar();

    setupPremiumInteractions();

    loadAnalytics();

});


/* ============================================================
   EVENT LISTENERS
   ============================================================ */

function setupEventListeners() {

    const district =
        document.getElementById("district");

    const taluk =
        document.getElementById("taluk");

    const village =
        document.getElementById("village");

    const propertyType =
        document.getElementById("propertyType");

    const bhk =
        document.getElementById("bhk");

    const searchButton =
        document.getElementById("searchButton");

    const refreshAnalytics =
        document.getElementById("refreshAnalytics");


    if (district) {

        district.addEventListener("change", () => {

            loadTaluks(district.value);

        });

    }


    if (taluk) {

        taluk.addEventListener("change", () => {

            loadVillages(taluk.value);

        });

    }


    if (propertyType) {

        propertyType.addEventListener("change", () => {

            updateBHKOptions();

        });

    }


    if (bhk) {

        bhk.addEventListener("change", () => {

            updateBHKOptions();

        });

    }


    if (searchButton) {

        searchButton.addEventListener(
            "click",
            performSearch
        );

    }


    if (refreshAnalytics) {

        refreshAnalytics.addEventListener(
            "click",
            loadAnalytics
        );

    }


    /* ========================================================
       ENTER KEY IN BUDGET
       ======================================================== */

    const budget =
        document.getElementById("budget");

    if (budget) {

        budget.addEventListener("keydown", event => {

            if (event.key === "Enter") {

                performSearch();

            }

        });

    }


    /* ========================================================
       NAVBAR SMOOTH SCROLLING
       ======================================================== */

    document.querySelectorAll(
        '.navbar .nav-inner > nav a[href^="#"]'
    ).forEach(link => {

        link.addEventListener("click", event => {

            const href =
                link.getAttribute("href");

            if (!href || href === "#") {

                event.preventDefault();

                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });

                return;

            }

            const target =
                document.querySelector(href);

            if (target) {

                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }

        });

    });


    /* ========================================================
       HERO BUTTONS
       ======================================================== */

    document.querySelectorAll(
        '.hero-buttons a[href^="#"]'
    ).forEach(link => {

        link.addEventListener("click", event => {

            const href =
                link.getAttribute("href");

            const target =
                document.querySelector(href);

            if (target) {

                event.preventDefault();

                target.scrollIntoView({
                    behavior: "smooth",
                    block: "start"
                });

            }

        });

    });

}


/* ============================================================
   LOAD DISTRICTS
   ============================================================ */

async function loadDistricts() {

    const district =
        document.getElementById("district");

    if (!district) return;


    district.innerHTML = `
        <option value="">
            Loading Districts...
        </option>
    `;


    try {

        const response =
            await fetch("/api/districts");


        if (!response.ok) {

            throw new Error(
                `District API returned ${response.status}`
            );

        }


        const data =
            await response.json();


        district.innerHTML = `
            <option value="">
                Select District
            </option>
        `;


        if (
            !Array.isArray(data) ||
            data.length === 0
        ) {

            district.innerHTML = `
                <option value="">
                    No Districts Found
                </option>
            `;

            return;

        }


        data.forEach(item => {

            const option =
                document.createElement("option");


            option.value =
                item.id;


            option.textContent =
                item.name;


            district.appendChild(
                option
            );

        });


    } catch (error) {

        console.error(
            "District loading error:",
            error
        );


        district.innerHTML = `
            <option value="">
                Unable to load Districts
            </option>
        `;

    }

}


/* ============================================================
   LOAD TALUKS
   ============================================================ */

async function loadTaluks(districtId) {

    const taluk =
        document.getElementById("taluk");

    const village =
        document.getElementById("village");


    if (!taluk) return;


    taluk.innerHTML = `
        <option value="">
            Loading Taluks...
        </option>
    `;


    taluk.disabled = true;


    if (village) {

        village.innerHTML = `
            <option value="">
                Select Village
            </option>
        `;

        village.disabled = true;

    }


    if (!districtId) {

        taluk.innerHTML = `
            <option value="">
                Select Taluk
            </option>
        `;

        taluk.disabled = false;


        if (village) {

            village.disabled = false;

        }

        return;

    }


    try {

        const response =
            await fetch(
                `/api/taluks/${encodeURIComponent(
                    districtId
                )}`
            );


        if (!response.ok) {

            throw new Error(
                `Taluk API returned ${response.status}`
            );

        }


        const data =
            await response.json();


        taluk.innerHTML = `
            <option value="">
                Select Taluk
            </option>
        `;


        if (
            !Array.isArray(data) ||
            data.length === 0
        ) {

            taluk.innerHTML = `
                <option value="">
                    No Taluks Found
                </option>
            `;

            return;

        }


        data.forEach(item => {

            const option =
                document.createElement("option");


            option.value =
                item.id;


            option.textContent =
                item.name;


            taluk.appendChild(
                option
            );

        });


    } catch (error) {

        console.error(
            "Taluk loading error:",
            error
        );


        taluk.innerHTML = `
            <option value="">
                Unable to load Taluks
            </option>
        `;

    } finally {

        taluk.disabled = false;


        if (village) {

            village.disabled = false;

        }

    }

}


/* ============================================================
   LOAD VILLAGES
   ============================================================ */

async function loadVillages(talukId) {

    const village =
        document.getElementById("village");


    if (!village) return;


    village.innerHTML = `
        <option value="">
            Loading Villages...
        </option>
    `;


    village.disabled = true;


    if (!talukId) {

        village.innerHTML = `
            <option value="">
                Select Village
            </option>
        `;


        village.disabled = false;

        return;

    }


    try {

        const url =
            `/api/villages/${encodeURIComponent(
                talukId
            )}`;


        console.log(
            "Loading villages from:",
            url
        );


        const response =
            await fetch(url);


        if (!response.ok) {

            throw new Error(
                `Village API returned ${response.status}`
            );

        }


        const data =
            await response.json();


        console.log(
            "Villages received:",
            data
        );


        village.innerHTML = `
            <option value="">
                Select Village
            </option>
        `;


        if (
            !Array.isArray(data) ||
            data.length === 0
        ) {

            village.innerHTML = `
                <option value="">
                    No Villages Found
                </option>
            `;

            return;

        }


        data.forEach(item => {

            const option =
                document.createElement("option");


            option.value =
                item.id;


            option.textContent =
                item.name;


            village.appendChild(
                option
            );

        });


    } catch (error) {

        console.error(
            "Village loading error:",
            error
        );


        village.innerHTML = `
            <option value="">
                Unable to load Villages
            </option>
        `;

    } finally {

        village.disabled = false;

    }

}


/* ============================================================
   BHK OPTIONS
   ============================================================ */

function updateBHKOptions() {

    const propertyType =
        document.getElementById(
            "propertyType"
        );

    const bhk =
        document.getElementById("bhk");


    if (!propertyType || !bhk) return;


    const currentValue =
        bhk.value;


    if (
        propertyType.value === "Plot"
    ) {

        bhk.value = "";

        bhk.disabled = true;

        bhk.style.opacity =
            "0.45";

    } else {

        bhk.disabled = false;

        bhk.style.opacity =
            "1";


        if (
            currentValue &&
            ![
                "1",
                "2",
                "3",
                "4",
                "5"
            ].includes(currentValue)
        ) {

            bhk.value = "";

        }

    }

}


/* ============================================================
   FORMAT PRICE
   ============================================================ */

function formatPrice(price) {

    const value =
        Number(price);


    if (!Number.isFinite(value)) {

        return "₹0";

    }


    if (value >= 10000000) {

        return (
            "₹" +
            (value / 10000000)
                .toFixed(2) +
            " Cr"
        );

    }


    if (value >= 100000) {

        return (
            "₹" +
            (value / 100000)
                .toFixed(2) +
            " L"
        );

    }


    return (
        "₹" +
        value.toLocaleString("en-IN")
    );

}


/* ============================================================
   FORMAT NUMBER
   ============================================================ */

function formatNumber(value) {

    const number =
        Number(value);


    if (!Number.isFinite(number)) {

        return "0";

    }


    return number.toLocaleString(
        "en-IN"
    );

}


/* ============================================================
   CREATE PROPERTY CARD
   ============================================================ */

function createPropertyCard(property) {

    const card =
        document.createElement("div");


    card.className =
        "property-card";


    const propertyType =
        property.property_type ||
        "—";


    const area =
        property.area_sqft
            ? formatNumber(
                property.area_sqft
            )
            : "—";


    const bhk =
        property.bhk
            ? property.bhk
            : "—";


    const pricePerSqft =
        property.price_per_sqft
            ? "₹" +
              Number(
                  property.price_per_sqft
              ).toLocaleString("en-IN")
            : "—";


    card.innerHTML = `

        <div class="property-card-content">

            <h3>
                ${escapeHtml(
                    property.title ||
                    "Property"
                )}
            </h3>


            <div class="property-location">

                ${escapeHtml(
                    property.village ||
                    "—"
                )},

                ${escapeHtml(
                    property.taluk ||
                    "—"
                )},

                ${escapeHtml(
                    property.district ||
                    "—"
                )}

            </div>


            <div class="property-details">

                <div>

                    <span>
                        Property Type
                    </span>

                    <strong>
                        ${escapeHtml(
                            propertyType
                        )}
                    </strong>

                </div>


                <div>

                    <span>
                        Area
                    </span>

                    <strong>
                        ${area} sqft
                    </strong>

                </div>


                <div>

                    <span>
                        BHK
                    </span>

                    <strong>
                        ${bhk}
                    </strong>

                </div>


                <div>

                    <span>
                        Price / Sqft
                    </span>

                    <strong>
                        ${pricePerSqft}
                    </strong>

                </div>

            </div>


            <div class="property-price">

                ${formatPrice(
                    property.price
                )}

            </div>


            <button
                type="button"
                class="compare-button"
                onclick="addToCompare(${property.id})"
            >

                Add to Compare

            </button>

        </div>

    `;


    return card;

}


/* ============================================================
   ESCAPE HTML
   ============================================================ */

function escapeHtml(value) {

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


/* ============================================================
   PERFORM SEARCH
   ============================================================ */

async function performSearch() {

    const district =
        document.getElementById(
            "district"
        )?.value || "";


    const taluk =
        document.getElementById(
            "taluk"
        )?.value || "";


    const village =
        document.getElementById(
            "village"
        )?.value || "";


    const propertyType =
        document.getElementById(
            "propertyType"
        )?.value || "";


    const bhk =
        document.getElementById(
            "bhk"
        )?.value || "";


    const budget =
        document.getElementById(
            "budget"
        )?.value || "";


    const button =
        document.getElementById(
            "searchButton"
        );


    if (button) {

        button.disabled = true;

        button.classList.add(
            "searching"
        );


        const span =
            button.querySelector("span");


        if (span) {

            span.textContent =
                "Searching...";

        }

    }


    try {

        const params =
            new URLSearchParams();


        if (district) {

            params.append(
                "district",
                district
            );

        }


        if (taluk) {

            params.append(
                "taluk",
                taluk
            );

        }


        if (village) {

            params.append(
                "village",
                village
            );

        }


        if (propertyType) {

            params.append(
                "propertyType",
                propertyType
            );

        }


        if (bhk) {

            params.append(
                "bhk",
                bhk
            );

        }


        if (budget) {

            params.append(
                "budget",
                budget
            );

        }


        const response =
            await fetch(
                `/api/properties?${params.toString()}`
            );


        if (!response.ok) {

            throw new Error(
                "Property search failed"
            );

        }


        const data =
            await response.json();


        allProperties =
            Array.isArray(data)
                ? data
                : [];


        displayResults(
            allProperties
        );


    } catch (error) {

        console.error(
            "Search error:",
            error
        );


        displayResults([]);


    } finally {

        if (button) {

            button.disabled = false;

            button.classList.remove(
                "searching"
            );


            const span =
                button.querySelector("span");


            if (span) {

                span.textContent =
                    "Search Properties";

            }

        }

    }

}


/* ============================================================
   DISPLAY RESULTS
   ============================================================ */

function displayResults(properties) {

    const resultsSection =
        document.getElementById(
            "results"
        );


    const resultContainer =
        document.getElementById(
            "propertyResults"
        );


    const resultCount =
        document.getElementById(
            "resultCount"
        );


    if (
        !resultsSection ||
        !resultContainer
    ) {

        return;

    }


    resultContainer.innerHTML = "";


    if (resultCount) {

        resultCount.textContent =
            `${properties.length} ${
                properties.length === 1
                    ? "property"
                    : "properties"
            } found`;

    }


    resultsSection.classList.remove(
        "hidden"
    );


    if (!properties.length) {

        resultContainer.innerHTML = `

            <div class="property-card">

                <div class="property-card-content">

                    <h3>
                        No properties found
                    </h3>

                    <div class="property-location">
                        Try changing your search filters.
                    </div>

                </div>

            </div>

        `;

    } else {

        properties.forEach(
            (property, index) => {

                const card =
                    createPropertyCard(
                        property
                    );


                card.style.opacity =
                    "0";


                card.style.transform =
                    "translateY(25px)";


                resultContainer.appendChild(
                    card
                );


                setTimeout(() => {

                    card.style.opacity =
                        "1";


                    card.style.transform =
                        "translateY(0)";

                }, index * 90);

            }
        );

    }


    setTimeout(() => {

        resultsSection.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    }, 120);

}


/* ============================================================
   COMPARISON BAR
   ============================================================ */

function createComparisonBar() {

    if (
        document.getElementById(
            "comparisonBar"
        )
    ) {

        return;

    }


    const bar =
        document.createElement("div");


    bar.id =
        "comparisonBar";


    bar.className =
        "comparison-bar";


    bar.innerHTML = `

        <div>

            <strong>
                Compare Properties
            </strong>

            <span
                id="comparisonCount"
            >
                0 selected
            </span>

        </div>


        <button
            type="button"
            id="compareNowButton"
        >
            Compare Now
        </button>

    `;


    document.body.appendChild(
        bar
    );


    const compareNowButton =
        document.getElementById(
            "compareNowButton"
        );


    if (compareNowButton) {

        compareNowButton.addEventListener(
            "click",
            showComparison
        );

    }


    updateComparisonBar();

}


/* ============================================================
   ADD TO COMPARE
   ============================================================ */

function addToCompare(propertyId) {

    const id =
        Number(propertyId);


    if (
        compareList.includes(id)
    ) {

        compareList =
            compareList.filter(
                item => item !== id
            );

    } else {

        if (
            compareList.length >= 3
        ) {

            alert(
                "You can compare up to 3 properties."
            );

            return;

        }


        compareList.push(id);

    }


    updateComparisonBar();

    updateCompareButtons();

}


/* ============================================================
   UPDATE COMPARISON BAR
   ============================================================ */

function updateComparisonBar() {

    const bar =
        document.getElementById(
            "comparisonBar"
        );


    const count =
        document.getElementById(
            "comparisonCount"
        );


    if (!bar) return;


    if (count) {

        count.textContent =
            `${compareList.length} selected`;

    }


    if (
        compareList.length > 0
    ) {

        bar.classList.add(
            "comparison-visible"
        );

    } else {

        bar.classList.remove(
            "comparison-visible"
        );

    }

}


/* ============================================================
   UPDATE COMPARE BUTTONS
   ============================================================ */

function updateCompareButtons() {

    document.querySelectorAll(
        ".compare-button"
    ).forEach(button => {

        const match =
            button.getAttribute(
                "onclick"
            )?.match(/\d+/);


        if (!match) return;


        const id =
            Number(match[0]);


        if (
            compareList.includes(id)
        ) {

            button.textContent =
                "✓ Added to Compare";


            button.style.background =
                "rgba(53,184,121,.14)";

        } else {

            button.textContent =
                "Add to Compare";


            button.style.background =
                "";

        }

    });

}


/* ============================================================
   SHOW COMPARISON
   ============================================================ */

function showComparison() {

    if (
        compareList.length < 2
    ) {

        alert(
            "Select at least 2 properties to compare."
        );

        return;

    }


    const selected =
        allProperties.filter(
            property =>
                compareList.includes(
                    Number(property.id)
                )
        );


    if (!selected.length) {

        alert(
            "Please perform a search first."
        );

        return;

    }


    const existing =
        document.getElementById(
            "comparisonModal"
        );


    if (existing) {

        existing.remove();

    }


    const modal =
        document.createElement("div");


    modal.id =
        "comparisonModal";


    modal.style.cssText = `

        position: fixed;
        inset: 0;
        z-index: 300;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        background: rgba(0,0,0,.72);
        backdrop-filter: blur(12px);

    `;


    const content =
        document.createElement("div");


    content.style.cssText = `

        width: min(1100px, 100%);
        max-height: 85vh;
        overflow: auto;
        padding: 28px;
        border-radius: 25px;
        background: #0b1812;
        border: 1px solid rgba(53,184,121,.20);
        box-shadow: 0 40px 100px rgba(0,0,0,.5);

    `;


    let table = `

        <div style="
            display:flex;
            align-items:center;
            justify-content:space-between;
            gap:20px;
            margin-bottom:25px;
        ">

            <div>

                <div style="
                    color:#d8ad5c;
                    font-size:9px;
                    letter-spacing:.16em;
                ">
                    PROPERTY COMPARISON
                </div>

                <h2 style="
                    margin-top:8px;
                    color:#f4f7f3;
                ">
                    Compare selected properties
                </h2>

            </div>


            <button
                type="button"
                id="closeComparison"
                style="
                    width:40px;
                    height:40px;
                    border-radius:50%;
                    border:1px solid rgba(255,255,255,.1);
                    background:rgba(255,255,255,.05);
                    color:white;
                    cursor:pointer;
                    font-size:18px;
                "
            >
                ×
            </button>

        </div>


        <div style="
            overflow-x:auto;
        ">

            <table style="
                width:100%;
                border-collapse:collapse;
                min-width:650px;
            ">

                <thead>

                    <tr>

                        <th style="
                            padding:13px;
                            text-align:left;
                            border-bottom:1px solid rgba(255,255,255,.08);
                            color:#9eaca5;
                        ">
                            Property
                        </th>
    `;


    selected.forEach(property => {

        table += `
            <th style="
                padding:13px;
                text-align:left;
                border-bottom:1px solid rgba(255,255,255,.08);
                color:#d8ad5c;
            ">
                ${escapeHtml(
                    property.title ||
                    "Property"
                )}
            </th>
        `;

    });


    table += `
                    </tr>
                </thead>

                <tbody>
    `;


    const rows = [

        [
            "Type",
            property =>
                property.property_type ||
                "—"
        ],

        [
            "District",
            property =>
                property.district ||
                "—"
        ],

        [
            "Taluk",
            property =>
                property.taluk ||
                "—"
        ],

        [
            "Village",
            property =>
                property.village ||
                "—"
        ],

        [
            "BHK",
            property =>
                property.bhk ||
                "—"
        ],

        [
            "Area",
            property =>
                property.area_sqft
                    ? formatNumber(
                        property.area_sqft
                    ) + " sqft"
                    : "—"
        ],

        [
            "Price",
            property =>
                formatPrice(
                    property.price
                )
        ],

        [
            "Price / Sqft",
            property =>
                property.price_per_sqft
                    ? "₹" +
                      Number(
                          property.price_per_sqft
                      ).toLocaleString(
                          "en-IN"
                      )
                    : "—"
        ]

    ];


    rows.forEach(
        ([label, getter]) => {

            table += `
                <tr>

                    <td style="
                        padding:13px;
                        border-bottom:1px solid rgba(255,255,255,.06);
                        color:#9eaca5;
                        font-size:12px;
                    ">
                        ${label}
                    </td>
            `;


            selected.forEach(property => {

                table += `
                    <td style="
                        padding:13px;
                        border-bottom:1px solid rgba(255,255,255,.06);
                        color:#eef5f0;
                        font-size:12px;
                    ">
                        ${escapeHtml(
                            getter(property)
                        )}
                    </td>
                `;

            });


            table += `
                </tr>
            `;

        }
    );


    table += `
                </tbody>

            </table>

        </div>

    `;


    content.innerHTML =
        table;


    modal.appendChild(
        content
    );


    document.body.appendChild(
        modal
    );


    document.body.style.overflow =
        "hidden";


    document
        .getElementById(
            "closeComparison"
        )
        ?.addEventListener(
            "click",
            closeComparison
        );


    modal.addEventListener(
        "click",
        event => {

            if (
                event.target === modal
            ) {

                closeComparison();

            }

        }
    );

}


/* ============================================================
   CLOSE COMPARISON
   ============================================================ */

function closeComparison() {

    const modal =
        document.getElementById(
            "comparisonModal"
        );


    if (modal) {

        modal.remove();

    }


    document.body.style.overflow =
        "";

}


/* ============================================================
   LOAD ANALYTICS
   ============================================================ */

async function loadAnalytics() {

    try {

        const response =
            await fetch(
                "/api/properties"
            );


        if (!response.ok) {

            throw new Error(
                "Unable to load analytics"
            );

        }


        const data =
            await response.json();


        allProperties =
            Array.isArray(data)
                ? data
                : [];


        updateAnalyticsStats(
            allProperties
        );


        updatePropertyTypeChart(
            allProperties
        );


        updateDistrictChart(
            allProperties
        );


        updateBHKChart(
            allProperties
        );


        updatePriceTable(
            allProperties
        );


    } catch (error) {

        console.error(
            "Analytics error:",
            error
        );

    }

}


/* ============================================================
   ANALYTICS STATISTICS
   ============================================================ */

function updateAnalyticsStats(properties) {

    const total =
        properties.length;


    const prices =
        properties
            .map(
                property =>
                    Number(property.price)
            )
            .filter(
                value =>
                    Number.isFinite(value)
            );


    const psf =
        properties
            .map(
                property =>
                    Number(
                        property.price_per_sqft
                    )
            )
            .filter(
                value =>
                    Number.isFinite(value)
            );


    const averagePrice =
        prices.length
            ? prices.reduce(
                (sum, value) =>
                    sum + value,
                0
            ) / prices.length
            : 0;


    const averagePsf =
        psf.length
            ? psf.reduce(
                (sum, value) =>
                    sum + value,
                0
            ) / psf.length
            : 0;


    const minPrice =
        prices.length
            ? Math.min(...prices)
            : 0;


    const maxPrice =
        prices.length
            ? Math.max(...prices)
            : 0;


    const totalElement =
        document.getElementById(
            "analyticsTotal"
        );


    const avgPriceElement =
        document.getElementById(
            "analyticsAvgPrice"
        );


    const avgPsfElement =
        document.getElementById(
            "analyticsAvgPsf"
        );


    const rangeElement =
        document.getElementById(
            "analyticsPriceRange"
        );


    if (totalElement) {

        totalElement.textContent =
            formatNumber(total);

    }


    if (avgPriceElement) {

        avgPriceElement.textContent =
            formatPrice(
                averagePrice
            );

    }


    if (avgPsfElement) {

        avgPsfElement.textContent =
            "₹" +
            Math.round(
                averagePsf
            ).toLocaleString(
                "en-IN"
            );

    }


    if (rangeElement) {

        rangeElement.textContent =
            prices.length
                ? `${formatPrice(
                    minPrice
                )} – ${formatPrice(
                    maxPrice
                )}`
                : "—";

    }

}


/* ============================================================
   GENERIC BAR CHART
   ============================================================ */

function renderBarChart(container, data) {

    if (!container) return;


    container.innerHTML = "";


    if (!data.length) {

        container.textContent =
            "No data available.";

        return;

    }


    const max =
        Math.max(
            ...data.map(
                item => item.value
            ),
            1
        );


    data.forEach(item => {

        const row =
            document.createElement("div");


        row.className =
            "analytics-bar-row";


        const label =
            document.createElement("span");


        label.textContent =
            item.label;


        const track =
            document.createElement("div");


        track.className =
            "analytics-bar-track";


        const fill =
            document.createElement("div");


        fill.className =
            "analytics-bar-fill";


        fill.style.width =
            `${(
                item.value / max
            ) * 100}%`;


        track.appendChild(
            fill
        );


        const count =
            document.createElement("strong");


        count.textContent =
            item.value;


        row.appendChild(
            label
        );


        row.appendChild(
            track
        );


        row.appendChild(
            count
        );


        container.appendChild(
            row
        );

    });

}


/* ============================================================
   PROPERTY TYPE CHART
   ============================================================ */

function updatePropertyTypeChart(properties) {

    const counts = {};


    properties.forEach(property => {

        const type =
            property.property_type ||
            "Unknown";


        counts[type] =
            (counts[type] || 0) + 1;

    });


    const data =
        Object.entries(counts)
            .map(
                ([label, value]) => ({
                    label,
                    value
                })
            )
            .sort(
                (a, b) =>
                    b.value - a.value
            );


    renderBarChart(
        document.getElementById(
            "propertyTypeChart"
        ),
        data
    );

}


/* ============================================================
   DISTRICT CHART
   ============================================================ */

function updateDistrictChart(properties) {

    const counts = {};


    properties.forEach(property => {

        const district =
            property.district ||
            "Unknown";


        counts[district] =
            (counts[district] || 0) + 1;

    });


    const data =
        Object.entries(counts)
            .map(
                ([label, value]) => ({
                    label,
                    value
                })
            )
            .sort(
                (a, b) =>
                    b.value - a.value
            );


    renderBarChart(
        document.getElementById(
            "districtChart"
        ),
        data
    );

}


/* ============================================================
   BHK CHART
   ============================================================ */

function updateBHKChart(properties) {

    const counts = {};


    properties.forEach(property => {

        const bhk =
            property.bhk;


        if (
            bhk === null ||
            bhk === undefined ||
            bhk === ""
        ) {

            return;

        }


        const label =
            `${bhk} BHK`;


        counts[label] =
            (counts[label] || 0) + 1;

    });


    const data =
        Object.entries(counts)
            .map(
                ([label, value]) => ({
                    label,
                    value
                })
            )
            .sort(
                (a, b) =>
                    a.label.localeCompare(
                        b.label,
                        undefined,
                        {
                            numeric: true
                        }
                    )
            );


    renderBarChart(
        document.getElementById(
            "bhkChart"
        ),
        data
    );

}


/* ============================================================
   PRICE ANALYSIS TABLE
   ============================================================ */

function updatePriceTable(properties) {

    const tbody =
        document.getElementById(
            "priceAnalysisTable"
        );


    if (!tbody) return;


    tbody.innerHTML = "";


    const sorted =
        [...properties].sort(
            (a, b) =>
                Number(a.price || 0) -
                Number(b.price || 0)
        );


    if (!sorted.length) {

        tbody.innerHTML = `
            <tr>
                <td colspan="4">
                    No data available.
                </td>
            </tr>
        `;

        return;

    }


    sorted.forEach(property => {

        const row =
            document.createElement("tr");


        row.innerHTML = `

            <td>
                ${escapeHtml(
                    property.title ||
                    "Property"
                )}
            </td>

            <td>
                ${escapeHtml(
                    property.property_type ||
                    "—"
                )}
            </td>

            <td>
                ${formatPrice(
                    property.price
                )}
            </td>

            <td>
                ${
                    property.price_per_sqft
                        ? "₹" +
                          Number(
                              property.price_per_sqft
                          ).toLocaleString(
                              "en-IN"
                          )
                        : "—"
                }
            </td>

        `;


        tbody.appendChild(
            row
        );

    });

}


/* ============================================================
   PREMIUM SCROLL INTERACTIONS
   ============================================================ */

function setupPremiumInteractions() {

    setupScrollReveal();

    setupPropertyAnimation();

    setupActiveNavbar();

    setupDashboardTilt();

    setupScrollProgress();

}


/* ============================================================
   SCROLL REVEAL
   ============================================================ */

function setupScrollReveal() {

    const sections =
        document.querySelectorAll(
            ".search-section, " +
            ".results-section, " +
            ".analytics-section, " +
            ".about-section"
        );


    if (!sections.length) return;


    sections.forEach(section => {

        section.classList.add(
            "reveal-on-scroll"
        );

    });


    if (
        !("IntersectionObserver" in window)
    ) {

        sections.forEach(section => {

            section.classList.add(
                "visible"
            );

        });

        return;

    }


    const observer =
        new IntersectionObserver(
            entries => {

                entries.forEach(entry => {

                    if (
                        entry.isIntersecting
                    ) {

                        entry.target.classList.add(
                            "visible"
                        );


                        observer.unobserve(
                            entry.target
                        );

                    }

                });

            },
            {
                threshold: .12
            }
        );


    sections.forEach(section => {

        observer.observe(
            section
        );

    });

}


/* ============================================================
   PROPERTY CARD ANIMATION
   ============================================================ */

function setupPropertyAnimation() {

    const results =
        document.getElementById(
            "propertyResults"
        );


    if (!results) return;


    const animateCards =
        () => {

            const cards =
                results.querySelectorAll(
                    ".property-card"
                );


            cards.forEach(
                (card, index) => {

                    if (
                        card.dataset.animated
                    ) {

                        return;

                    }


                    card.dataset.animated =
                        "true";


                    card.style.opacity =
                        "0";


                    card.style.transform =
                        "translateY(25px)";


                    card.style.transition =
                        "opacity .5s ease, " +
                        "transform .5s cubic-bezier(.2,.8,.2,1)";


                    setTimeout(() => {

                        card.style.opacity =
                            "1";


                        card.style.transform =
                            "translateY(0)";

                    }, index * 90);

                }
            );

        };


    const observer =
        new MutationObserver(
            animateCards
        );


    observer.observe(
        results,
        {
            childList: true,
            subtree: true
        }
    );


    animateCards();

}


/* ============================================================
   ACTIVE NAVBAR
   ============================================================ */

function setupActiveNavbar() {

    const navLinks =
        document.querySelectorAll(
            ".navbar .nav-inner > nav a"
        );


    if (!navLinks.length) return;


    const sections = [

        document.querySelector(
            ".hero"
        ),

        document.querySelector(
            ".search-section"
        ),

        document.querySelector(
            ".analytics-section"
        ),

        document.querySelector(
            ".about-section"
        )

    ].filter(Boolean);


    function updateActiveNav() {

        let current =
            sections[0];


        sections.forEach(section => {

            const top =
                section.getBoundingClientRect()
                    .top;


            if (top <= 160) {

                current =
                    section;

            }

        });


        navLinks.forEach(link => {

            link.classList.remove(
                "nav-active"
            );


            const href =
                link.getAttribute(
                    "href"
                );


            if (
                current &&
                href &&
                href !== "#" &&
                current.matches(href)
            ) {

                link.classList.add(
                    "nav-active"
                );

            }

        });

    }


    window.addEventListener(
        "scroll",
        updateActiveNav,
        {
            passive: true
        }
    );


    updateActiveNav();

}


/* ============================================================
   DASHBOARD MOUSE TILT
   ============================================================ */

function setupDashboardTilt() {

    const dashboard =
        document.querySelector(
            ".dashboard-card"
        );


    if (
        !dashboard ||
        window.innerWidth <= 900
    ) {

        return;

    }


    dashboard.addEventListener(
        "mousemove",
        event => {

            const rect =
                dashboard.getBoundingClientRect();


            const x =
                event.clientX -
                rect.left;


            const y =
                event.clientY -
                rect.top;


            const rotateY =
                (
                    x / rect.width -
                    .5
                ) * 5;


            const rotateX =
                (
                    y / rect.height -
                    .5
                ) * -5;


            dashboard.style.animation =
                "none";


            dashboard.style.transform =
                `perspective(900px)
                 rotateX(${rotateX}deg)
                 rotateY(${rotateY}deg)
                 translateY(-8px)`;

        }
    );


    dashboard.addEventListener(
        "mouseleave",
        () => {

            dashboard.style.transform =
                "";

            dashboard.style.animation =
                "";

        }
    );

}


/* ============================================================
   SCROLL PROGRESS
   ============================================================ */

function setupScrollProgress() {

    const progress =
        document.createElement(
            "div"
        );


    progress.id =
        "scrollProgress";


    progress.style.cssText = `

        position: fixed;
        top: 0;
        left: 0;
        z-index: 500;
        width: 0%;
        height: 2px;
        background: linear-gradient(
            90deg,
            #35b879,
            #d8ad5c
        );
        box-shadow: 0 0 12px rgba(53,184,121,.4);
        pointer-events: none;
        transition: width .08s linear;

    `;


    document.body.appendChild(
        progress
    );


    function updateProgress() {

        const scrollTop =
            window.scrollY;


        const documentHeight =
            document.documentElement
                .scrollHeight -
            window.innerHeight;


        if (
            documentHeight <= 0
        ) {

            progress.style.width =
                "0%";

            return;

        }


        const percentage =
            (
                scrollTop /
                documentHeight
            ) * 100;


        progress.style.width =
            `${percentage}%`;

    }


    window.addEventListener(
        "scroll",
        updateProgress,
        {
            passive: true
        }
    );


    updateProgress();

}


/* ============================================================
   EXPOSE FUNCTIONS FOR INLINE HTML
   ============================================================ */

window.addToCompare =
    addToCompare;

window.performSearch =
    performSearch;

window.closeComparison =
    closeComparison;