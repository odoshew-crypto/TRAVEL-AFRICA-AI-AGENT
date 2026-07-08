const statusBox = document.getElementById("status");
const answerBox = document.getElementById("answer");
const hotelList = document.getElementById("hotelList");
const sourcesList = document.getElementById("sourcesList");
const travelForm = document.getElementById("travelForm");
const questionInput = document.getElementById("question");
const submitButton = travelForm?.querySelector("button[type='submit']");

const state = {
    hotels: [],
    sources: []
};

function escapeHtml(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/\"/g, "&quot;");
}

function updateStatus(message, type = "") {
    if (!statusBox) return;
    statusBox.textContent = message;
    statusBox.className = `status-pill ${type}`.trim();
}

function setLoading(isLoading) {
    if (!submitButton) return;
    submitButton.classList.toggle("is-loading", isLoading);
    submitButton.disabled = isLoading;
    const label = submitButton.querySelector(".btn-label");
    if (label) {
        label.textContent = isLoading ? "Thinking..." : "Plan my trip";
    }
}

function renderHotels(hotels, sources = []) {
    if (!hotelList) return;

    if (!hotels || hotels.length === 0) {
        hotelList.innerHTML = '<p class="empty-state">No hotel cards available yet. Try asking the AI for a destination.</p>';
        return;
    }

    const sourceNames = new Set((sources || []).map((source) => String(source.hotel_name || "").trim().toLowerCase()));
    const matchingHotels = hotels.filter((hotel) => sourceNames.has(String(hotel.hotel_name || "").trim().toLowerCase()));
    const displayHotels = matchingHotels.length > 0 ? matchingHotels : hotels.slice(0, 4);

    hotelList.innerHTML = displayHotels.map((hotel) => {
        const website = hotel.website_url || "";
        const description = hotel.description || "A refined stay with thoughtful amenities and exceptional service.";
        const country = hotel.country || "East Africa";
        const location = hotel.location || "Featured destination";
        const rating = hotel.rating || "4.7";

        return `
            <article class="hotel-card">
                <div class="hotel-top">
                    <div>
                        <h3>${escapeHtml(hotel.hotel_name || "Luxury stay")}</h3>
                        <p class="hotel-location">${escapeHtml(country)} • ${escapeHtml(location)}</p>
                    </div>
                    <span class="rating-pill">★ ${escapeHtml(rating)}</span>
                </div>
                <p class="hotel-description">${escapeHtml(description)}</p>
                <div class="hotel-footer">
                    <span class="hotel-meta">Curated for premium travel stays</span>
                    ${website ? `<a class="hotel-link" href="${escapeHtml(website)}" target="_blank" rel="noopener noreferrer">Visit website</a>` : ""}
                </div>
            </article>
        `;
    }).join("");
}

function renderSources(sources = []) {
    if (!sourcesList) return;

    if (!sources || sources.length === 0) {
        sourcesList.innerHTML = '<li><span class="empty-state">No source references available yet.</span></li>';
        return;
    }

    sourcesList.innerHTML = sources.map((source) => {
        const label = source.hotel_name || "Recommended stay";
        const location = source.location || "East Africa";
        const url = source.source_url || "";
        return `
            <li>
                <strong>${escapeHtml(label)}</strong>
                <div>${escapeHtml(location)}</div>
                ${url ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Open reference</a>` : ""}
            </li>
        `;
    }).join("");
}

async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Request failed");
    }
    return data;
}

async function loadHotels() {
    try {
        const hotels = await requestJson("/hotels");
        state.hotels = Array.isArray(hotels) ? hotels : [];
        renderHotels(state.hotels, state.sources);
    } catch (error) {
        console.error(error);
        renderHotels([]);
    }
}

async function askQuestion(event) {
    if (event) {
        event.preventDefault();
    }

    const question = questionInput?.value?.trim() || "";
    if (!question) {
        updateStatus("Please share your travel idea first.", "error");
        return;
    }

    setLoading(true);
    updateStatus("Crafting your East African escape...", "loading");
    answerBox.classList.add("loading");
    answerBox.innerHTML = `
        <div class="loader">
            <span class="dot"></span>
            <span>Preparing recommendations</span>
        </div>
    `;

    try {
        const data = await requestJson("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ question })
        });

        const answerText = data.answer || "No answer returned yet.";
        const sources = Array.isArray(data.sources) ? data.sources : [];
        state.sources = sources;

        answerBox.classList.remove("loading");
        answerBox.innerHTML = `<div>${escapeHtml(answerText).replace(/\n/g, "<br>")}</div>`;
        renderHotels(state.hotels, sources);
        renderSources(sources);
        updateStatus("Recommendations are ready.", "success");
    } catch (error) {
        answerBox.classList.remove("loading");
        answerBox.innerHTML = '<p class="empty-state">The assistant is unavailable right now. Please try again shortly.</p>';
        updateStatus(error.message, "error");
        console.error(error);
    } finally {
        setLoading(false);
    }
}

function attachChipEvents() {
    document.querySelectorAll(".chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            const query = chip.dataset.query || "";
            if (questionInput) {
                questionInput.value = query;
            }
            askQuestion();
        });
    });
}

window.addEventListener("DOMContentLoaded", () => {
    travelForm?.addEventListener("submit", askQuestion);
    attachChipEvents();
    loadHotels();
});
