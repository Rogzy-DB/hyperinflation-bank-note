/**
 * Hyperinflation Banknote Visualizer
 * Main Application JavaScript
 */

// State
let periodsData = [];
let filteredPeriods = [];

// DOM Elements
const elements = {
    periodsGrid: document.getElementById('periodsGrid'),
    searchInput: document.getElementById('searchInput'),
    sortSelect: document.getElementById('sortSelect'),
    decadeSelect: document.getElementById('decadeSelect'),
    downloadAllBtn: document.getElementById('downloadAllBtn'),
    noResults: document.getElementById('noResults'),
    totalPeriods: document.getElementById('totalPeriods'),
    totalCountries: document.getElementById('totalCountries'),
    totalBills: document.getElementById('totalBills'),
    worstInflation: document.getElementById('worstInflation'),
    cardTemplate: document.getElementById('periodCardTemplate')
};

// Flag API URL (using flagcdn.com for free flags)
const getFlagUrl = (countryCode) => {
    return `https://flagcdn.com/w80/${countryCode.toLowerCase()}.png`;
};

// Initialize app
async function init() {
    try {
        await loadPeriodsData();
        updateStats();
        // Sort by bill count by default
        filteredPeriods.sort((a, b) => (b.bills?.length || 0) - (a.bills?.length || 0));
        renderAllPeriods();
        setupEventListeners();
    } catch (error) {
        console.error('Failed to initialize app:', error);
        showError('Failed to load data. Please refresh the page.');
    }
}

// Load periods data from JSON
async function loadPeriodsData() {
    const response = await fetch('data/periods.json');
    if (!response.ok) throw new Error('Failed to load periods data');
    const data = await response.json();
    periodsData = data.periods;
    filteredPeriods = [...periodsData];
}

// Update statistics in the stats bar
function updateStats() {
    const countries = new Set(periodsData.map(p => p.country));
    const totalBills = periodsData.reduce((sum, p) => sum + (p.bills?.length || 0), 0);

    // Turkey is kept as a contrast case: it is not counted as a hyperinflation
    elements.totalPeriods.textContent = periodsData.filter(p => p.kind !== 'chronic').length;
    elements.totalCountries.textContent = countries.size;
    elements.totalBills.textContent = totalBills;

    // Worst single month in the data (peakMonthlyPct is a number; display string beside it)
    const worst = periodsData
        .filter(p => typeof p.peakMonthlyPct === 'number')
        .reduce((a, b) => (b.peakMonthlyPct > a.peakMonthlyPct ? b : a));
    elements.worstInflation.textContent = worst.peakInflation;
}

// Create a period card element
function createPeriodCard(period) {
    const template = elements.cardTemplate.content.cloneNode(true);
    const card = template.querySelector('.period-card');

    card.dataset.periodId = period.id;

    // Image: the first banknote of the period
    const img = card.querySelector('.card-image img');
    if (period.bills?.[0]) {
        img.src = `assets/bills/thumbnails/${period.bills[0].replace('.png', '.jpg')}`;
        img.alt = (period.billLabels && period.billLabels[period.bills[0]]) || `${period.country} banknote`;
        img.onerror = () => { img.remove(); };
    } else {
        // no note in the collection yet: an empty frame, not a placeholder picture
        img.remove();
        card.querySelector('.card-image').classList.add('card-image-empty');
        card.querySelector('.card-image').dataset.empty = 'No banknote in the collection yet';
    }

    // Badge for featured or ongoing
    const badge = card.querySelector('.card-badge');
    if (period.kind === 'chronic') {
        badge.textContent = 'Not a hyperinflation';
        badge.title = 'Chronic high inflation that never reached 50% in a month, shown for contrast';
    } else if (period.periodEnd === 'present') {
        badge.textContent = 'Ongoing';
    } else if (period.featured) {
        badge.textContent = 'Notable';
    }

    // Flag
    const flag = card.querySelector('.card-flag');
    if (!period.countryCode) flag.remove();
    else flag.src = getFlagUrl(period.countryCode);
    flag.alt = `${period.country} flag`;
    flag.onerror = () => {
        flag.style.display = 'none';
    };

    // Title and period
    card.querySelector('.card-title').textContent = period.country;
    card.querySelector('.card-period').textContent = `${period.periodStart}–${period.periodEnd}`;

    // Stats
    card.querySelector('.peak-inflation').textContent = period.peakInflation;
    card.querySelector('.bill-count').textContent = period.bills?.length || 0;

    // Currency
    card.querySelector('.card-currency').textContent = period.currency;

    // Link
    const link = card.querySelector('.card-link');
    link.href = `pages/${period.id}.html`;

    // Click handler for the whole card
    card.addEventListener('click', (e) => {
        if (e.target.tagName !== 'A') {
            window.location.href = `pages/${period.id}.html`;
        }
    });

    return card;
}

// Render all periods (filtered)
function renderAllPeriods() {
    elements.periodsGrid.innerHTML = '';

    if (filteredPeriods.length === 0) {
        elements.noResults.style.display = 'block';
        return;
    }

    elements.noResults.style.display = 'none';

    filteredPeriods.forEach(period => {
        elements.periodsGrid.appendChild(createPeriodCard(period));
    });
}

// Filter and sort periods
function filterAndSortPeriods() {
    const searchTerm = elements.searchInput.value.toLowerCase().trim();
    const sortBy = elements.sortSelect.value;
    const decade = elements.decadeSelect.value;

    // Filter
    filteredPeriods = periodsData.filter(period => {
        // Search filter
        const matchesSearch = !searchTerm ||
            period.country.toLowerCase().includes(searchTerm) ||
            period.currency.toLowerCase().includes(searchTerm) ||
            period.periodStart.includes(searchTerm) ||
            period.periodEnd.includes(searchTerm);

        // Decade filter
        const matchesDecade = !decade ||
            (parseInt(period.periodStart) >= parseInt(decade) &&
                parseInt(period.periodStart) < parseInt(decade) + 10);

        return matchesSearch && matchesDecade;
    });

    // Sort
    filteredPeriods.sort((a, b) => {
        switch (sortBy) {
            case 'date':
                return parseInt(a.periodStart) - parseInt(b.periodStart);
            case 'country':
                return a.country.localeCompare(b.country);
            case 'bills':
                return (b.bills?.length || 0) - (a.bills?.length || 0);
            case 'severity':
            default:
                // worst single month first; a period without one (Turkey) goes last
                return (b.peakMonthlyPct ?? -1) - (a.peakMonthlyPct ?? -1);
        }
    });

    renderAllPeriods();
}

// Setup event listeners
function setupEventListeners() {
    // Search input with debounce
    let searchTimeout;
    elements.searchInput.addEventListener('input', () => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(filterAndSortPeriods, 300);
    });

    // Sort and filter selects
    elements.sortSelect.addEventListener('change', filterAndSortPeriods);
    elements.decadeSelect.addEventListener('change', filterAndSortPeriods);

    // Download all button
    elements.downloadAllBtn.addEventListener('click', handleDownloadAll);
}

// Handle download all bills
async function handleDownloadAll() {
    const btn = elements.downloadAllBtn;
    const originalText = btn.innerHTML;

    // Update button state
    btn.disabled = true;
    btn.innerHTML = `
        <svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-dasharray="60" stroke-dashoffset="20"/>
        </svg>
        <span>Preparing ZIP...</span>
    `;

    try {
        await loadJSZip();
        const zip = new JSZip();

        // Collect all bills from all periods
        const allBills = [];
        periodsData.forEach(period => {
            if (period.bills && period.bills.length > 0) {
                period.bills.forEach(bill => {
                    allBills.push({
                        filename: bill,
                        folder: `${period.country} (${period.periodStart}-${period.periodEnd})`
                    });
                });
            }
        });

        if (allBills.length === 0) {
            alert('No bills available to download.');
            return;
        }

        // Update button with progress
        let downloaded = 0;
        const total = allBills.length;

        // Download each bill and add to ZIP
        const downloadPromises = allBills.map(async (billInfo) => {
            const webPath = `assets/bills/web/${billInfo.filename.replace('.png', '.jpg')}`;
            const originalPath = `assets/bills/originals/${billInfo.filename}`;

            try {
                // Try web version first
                let response = await fetch(webPath);
                let filename = billInfo.filename.replace('.png', '.jpg');

                // Fallback to original if web version not found
                if (!response.ok) {
                    response = await fetch(originalPath);
                    filename = billInfo.filename;
                }

                if (response.ok) {
                    const blob = await response.blob();
                    zip.folder(billInfo.folder).file(filename, blob);
                }
            } catch (error) {
                console.warn(`Failed to download: ${billInfo.filename}`);
            }

            downloaded++;
            btn.innerHTML = `
                <svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" stroke-dasharray="60" stroke-dashoffset="20"/>
                </svg>
                <span>${downloaded}/${total} bills...</span>
            `;
        });

        await Promise.all(downloadPromises);

        // Generate and download ZIP
        btn.innerHTML = `
            <svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" stroke-dasharray="60" stroke-dashoffset="20"/>
            </svg>
            <span>Creating ZIP...</span>
        `;

        const content = await zip.generateAsync({ type: 'blob' });

        // Create download link
        const url = URL.createObjectURL(content);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'hyperinflation-banknotes-collection.zip';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Download failed:', error);
        alert('Failed to create download. Please try again.');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Load JSZip only when someone actually downloads (saves ~95 KB on every page view)
function loadJSZip() {
    if (window.JSZip) return Promise.resolve();
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/jszip@3.10.1/dist/jszip.min.js';
        script.onload = resolve;
        script.onerror = () => reject(new Error('Failed to load JSZip'));
        document.head.appendChild(script);
    });
}

// Show error message
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.innerHTML = `
        <p>${message}</p>
        <button onclick="location.reload()">Retry</button>
    `;
    document.querySelector('.main-content').prepend(errorDiv);
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
