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

    elements.totalPeriods.textContent = periodsData.length;
    elements.totalCountries.textContent = countries.size;
    elements.totalBills.textContent = totalBills;

    // Find worst inflation (Hungary 1946 is historically the worst)
    const hungary = periodsData.find(p => p.id === 'hungary-1945-1946');
    if (hungary) {
        elements.worstInflation.textContent = '41.9 quadrillion %';
    }
}

// Create a period card element
function createPeriodCard(period) {
    const template = elements.cardTemplate.content.cloneNode(true);
    const card = template.querySelector('.period-card');

    card.dataset.periodId = period.id;

    // Image - use placeholder or first bill thumbnail
    const img = card.querySelector('.card-image img');
    const thumbnailPath = period.bills?.[0]
        ? `assets/bills/thumbnails/${period.bills[0].replace('.png', '.jpg')}`
        : 'assets/placeholder.jpg';
    img.src = thumbnailPath;
    img.alt = `${period.country} ${period.currency} banknote`;
    img.onerror = () => {
        img.src = `https://placehold.co/400x200/1a1a1a/666?text=${encodeURIComponent(period.country)}`;
    };

    // Badge for featured or ongoing
    const badge = card.querySelector('.card-badge');
    if (period.periodEnd === 'present') {
        badge.textContent = 'Ongoing';
    } else if (period.featured) {
        badge.textContent = 'Notable';
    }

    // Flag
    const flag = card.querySelector('.card-flag');
    flag.src = getFlagUrl(period.countryCode);
    flag.alt = `${period.country} flag`;
    flag.onerror = () => {
        flag.style.display = 'none';
    };

    // Title and period
    card.querySelector('.card-title').textContent = period.country;
    card.querySelector('.card-period').textContent = `${period.periodStart} - ${period.periodEnd}`;

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
                // Sort by featured first, then by approximate severity
                if (a.featured !== b.featured) return b.featured ? 1 : -1;
                return getSeverityScore(b) - getSeverityScore(a);
        }
    });

    renderAllPeriods();
}

// Get approximate severity score for sorting
function getSeverityScore(period) {
    const inflation = period.peakInflation.toLowerCase();
    if (inflation.includes('quadrillion')) return 100;
    if (inflation.includes('trillion')) return 90;
    if (inflation.includes('billion')) return 80;
    if (inflation.includes('million')) return 70;
    if (inflation.includes('thousand') || inflation.includes('000%')) return 60;
    return 50;
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
        Preparing ZIP...
    `;

    try {
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
                ${downloaded}/${total} bills...
            `;
        });

        await Promise.all(downloadPromises);

        // Generate and download ZIP
        btn.innerHTML = `
            <svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10" stroke-dasharray="60" stroke-dashoffset="20"/>
            </svg>
            Creating ZIP...
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
