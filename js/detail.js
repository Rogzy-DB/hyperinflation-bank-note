/**
 * Hyperinflation Banknote Visualizer
 * Detail Page JavaScript
 */

let periodData = null;
let exchangeRateData = null;
let booksData = null;
let currentBillIndex = 0;
let chart = null;

// DOM Elements
const elements = {
    countryFlag: document.getElementById('countryFlag'),
    heroTitle: document.getElementById('heroTitle'),
    heroPeriod: document.getElementById('heroPeriod'),
    heroCurrency: document.getElementById('heroCurrency'),
    statPeakInflation: document.getElementById('statPeakInflation'),
    statPeakMonth: document.getElementById('statPeakMonth'),
    statExchangeRate: document.getElementById('statExchangeRate'),
    statBillCount: document.getElementById('statBillCount'),
    billsGallery: document.getElementById('billsGallery'),
    infoContent: document.getElementById('infoContent'),
    factCause: document.getElementById('factCause'),
    factResolution: document.getElementById('factResolution'),
    chartSubtitle: document.getElementById('chartSubtitle'),
    chartNote: document.getElementById('chartNote'),
    downloadPeriodBtn: document.getElementById('downloadPeriodBtn'),
    lightbox: document.getElementById('lightbox'),
    lightboxImage: document.getElementById('lightboxImage'),
    lightboxCaption: document.getElementById('lightboxCaption'),
    lightboxClose: document.getElementById('lightboxClose'),
    lightboxPrev: document.getElementById('lightboxPrev'),
    lightboxNext: document.getElementById('lightboxNext'),
    booksSection: document.getElementById('booksSection'),
    booksGallery: document.getElementById('booksGallery')
};

// Flag API URL
const getFlagUrl = (countryCode) => {
    return `https://flagcdn.com/w160/${countryCode.toLowerCase()}.png`;
};

// Initialize detail page
async function initDetailPage(periodId) {
    try {
        await loadPeriodData(periodId);
        if (!periodData) {
            showError('Period not found');
            return;
        }

        updatePageContent();
        renderBillsGallery();
        await loadExchangeRateData(periodId);
        await loadBooksData(periodId);
        await loadInfoContent(periodId);
        setupEventListeners();
        updateDocumentTitle();
    } catch (error) {
        console.error('Failed to initialize detail page:', error);
        showError('Failed to load period data');
    }
}

// Load period data from JSON
async function loadPeriodData(periodId) {
    const response = await fetch('../data/periods.json');
    if (!response.ok) throw new Error('Failed to load periods data');
    const data = await response.json();
    periodData = data.periods.find(p => p.id === periodId);
}

// Load exchange rate data
async function loadExchangeRateData(periodId) {
    try {
        const response = await fetch(`../data/exchange-rates/${periodId}.json`);
        if (response.ok) {
            exchangeRateData = await response.json();
            renderChart();
        } else {
            elements.chartNote.textContent = 'Exchange rate data not yet available for this period.';
        }
    } catch (error) {
        console.log('No exchange rate data available');
        elements.chartNote.textContent = 'Exchange rate data not yet available for this period.';
    }
}

// Load books data
async function loadBooksData(periodId) {
    try {
        const response = await fetch(`../data/books/${periodId}.json`);
        if (response.ok) {
            booksData = await response.json();
            renderBooksGallery();
        }
    } catch (error) {
        console.log('No books data available for this period');
    }
}

// Render books gallery
function renderBooksGallery() {
    if (!booksData || !booksData.books || booksData.books.length === 0) {
        return;
    }

    // Show the books section
    elements.booksSection.style.display = 'block';

    elements.booksGallery.innerHTML = booksData.books.map(book => {
        // Use Open Library Covers API with ISBN, fallback to placeholder
        const coverUrl = book.isbn
            ? `https://covers.openlibrary.org/b/isbn/${book.isbn}-L.jpg`
            : `../assets/books/${book.cover}`;
        const placeholderCover = `https://placehold.co/200x280/1a1a1a/d4af37?text=${encodeURIComponent(book.title)}`;

        return `
            <a href="${book.link}" target="_blank" rel="noopener" class="book-card">
                <img class="book-card-cover"
                     src="${coverUrl}"
                     alt="${book.title} cover"
                     onerror="this.src='${placeholderCover}'">
                <div class="book-card-info">
                    <h4 class="book-card-title">${book.title}</h4>
                    <p class="book-card-author">${book.author}</p>
                    <p class="book-card-year">${book.year}</p>
                    <p class="book-card-description">${book.description}</p>
                </div>
            </a>
        `;
    }).join('');
}

// Load markdown info content
async function loadInfoContent(periodId) {
    try {
        const response = await fetch(`../content/${periodId}/info.md`);
        if (response.ok) {
            const markdown = await response.text();
            elements.infoContent.innerHTML = marked.parse(markdown);
        } else {
            elements.infoContent.innerHTML = `
                <p>Historical information for this period is being compiled.</p>
                <p><strong>Summary:</strong> ${periodData.country} experienced severe hyperinflation
                during ${periodData.periodStart}-${periodData.periodEnd}, with the ${periodData.currency}
                losing most of its value.</p>
                <p><strong>Cause:</strong> ${periodData.cause}</p>
                <p><strong>Resolution:</strong> ${periodData.resolution}</p>
            `;
        }
    } catch (error) {
        elements.infoContent.innerHTML = '<p>Information coming soon.</p>';
    }
}

// Update page content with period data
function updatePageContent() {
    // Flag
    elements.countryFlag.src = getFlagUrl(periodData.countryCode);
    elements.countryFlag.alt = `${periodData.country} flag`;

    // Hero info
    elements.heroTitle.textContent = `${periodData.country} Hyperinflation`;
    elements.heroPeriod.textContent = `${periodData.periodStart} - ${periodData.periodEnd}`;
    elements.heroCurrency.textContent = periodData.currency;

    // Stats
    elements.statPeakInflation.textContent = periodData.peakInflation;
    elements.statPeakMonth.textContent = periodData.peakMonth;
    elements.statExchangeRate.textContent = periodData.exchangeRatePeak;
    elements.statBillCount.textContent = periodData.bills?.length || 0;

    // Facts
    elements.factCause.textContent = periodData.cause;
    elements.factResolution.textContent = periodData.resolution;

    // Chart subtitle
    elements.chartSubtitle.textContent = `${periodData.currency} per 1 USD (logarithmic scale)`;
}

// Update document title
function updateDocumentTitle() {
    document.title = `${periodData.country} Hyperinflation (${periodData.periodStart}-${periodData.periodEnd}) - Hyperinflation Archive`;
}

// Render bills gallery
function renderBillsGallery() {
    if (!periodData.bills || periodData.bills.length === 0) {
        elements.billsGallery.innerHTML = '<p class="no-bills">No banknotes available yet.</p>';
        return;
    }

    elements.billsGallery.innerHTML = periodData.bills.map((bill, index) => {
        const billName = formatBillName(bill);
        const webPath = `../assets/bills/web/${bill.replace('.png', '.jpg')}`;
        const thumbPath = `../assets/bills/thumbnails/${bill.replace('.png', '.jpg')}`;

        return `
            <div class="bill-card" data-index="${index}" data-bill="${bill}">
                <img src="${thumbPath}"
                     alt="${billName}"
                     loading="lazy"
                     onerror="this.src='https://placehold.co/300x180/1a1a1a/666?text=${encodeURIComponent(billName)}'">
                <div class="bill-card-info">
                    <p class="bill-card-name">${billName}</p>
                    <p class="bill-card-denomination">${periodData.currency}</p>
                </div>
            </div>
        `;
    }).join('');

    // Add click handlers
    document.querySelectorAll('.bill-card').forEach(card => {
        card.addEventListener('click', () => {
            const index = parseInt(card.dataset.index);
            openLightbox(index);
        });
    });
}

// Format bill filename to readable name
function formatBillName(filename) {
    return filename
        .replace(/\.(png|jpg|jpeg)$/i, '')
        .replace(/^F\d+-\d+\s*/, '') // Remove F2-X prefixes
        .replace(/_/g, ' ')
        .replace(/(\d+)([a-zA-Z])/g, '$1 $2')
        .replace(/([a-zA-Z])(\d)/g, '$1 $2')
        .trim();
}

// Render exchange rate chart
function renderChart() {
    if (!exchangeRateData || !exchangeRateData.dataPoints) return;

    const ctx = document.getElementById('exchangeRateChart').getContext('2d');

    // Destroy existing chart if any
    if (chart) {
        chart.destroy();
    }

    const labels = exchangeRateData.dataPoints.map(d => d.date);
    const data = exchangeRateData.dataPoints.map(d => d.rate);

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: `${exchangeRateData.currency} per USD`,
                data: data,
                borderColor: '#d4af37',
                backgroundColor: 'rgba(212, 175, 55, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 3,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a0a0a0',
                        maxTicksLimit: 8
                    }
                },
                y: {
                    type: exchangeRateData.useLogScale ? 'logarithmic' : 'linear',
                    grid: {
                        color: 'rgba(255, 255, 255, 0.1)'
                    },
                    ticks: {
                        color: '#a0a0a0',
                        callback: function(value) {
                            return formatLargeNumber(value);
                        }
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1a1a1a',
                    titleColor: '#f5f5f5',
                    bodyColor: '#a0a0a0',
                    borderColor: '#333',
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            return `${formatLargeNumber(context.raw)} ${exchangeRateData.currency}/USD`;
                        }
                    }
                }
            }
        }
    });

    // Add chart note
    if (exchangeRateData.sources) {
        elements.chartNote.textContent = `Source: ${exchangeRateData.sources.join(', ')}`;
    }
}

// Format large numbers for display
function formatLargeNumber(num) {
    if (num >= 1e12) return (num / 1e12).toFixed(1) + 'T';
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toFixed(0);
}

// Lightbox functions
function openLightbox(index) {
    currentBillIndex = index;
    updateLightboxContent();
    elements.lightbox.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeLightbox() {
    elements.lightbox.classList.remove('active');
    document.body.style.overflow = '';
}

function updateLightboxContent() {
    const bill = periodData.bills[currentBillIndex];
    const webPath = `../assets/bills/web/${bill.replace('.png', '.jpg')}`;
    const originalPath = `../assets/bills/originals/${bill}`;

    // Try web version first, fallback to original
    elements.lightboxImage.src = webPath;
    elements.lightboxImage.onerror = () => {
        elements.lightboxImage.src = originalPath;
    };
    elements.lightboxImage.alt = formatBillName(bill);
    elements.lightboxCaption.textContent = `${formatBillName(bill)} - ${periodData.currency}`;
}

function navigateLightbox(direction) {
    const totalBills = periodData.bills.length;
    currentBillIndex = (currentBillIndex + direction + totalBills) % totalBills;
    updateLightboxContent();
}

// Setup event listeners
function setupEventListeners() {
    // Lightbox controls
    elements.lightboxClose.addEventListener('click', closeLightbox);
    elements.lightboxPrev.addEventListener('click', () => navigateLightbox(-1));
    elements.lightboxNext.addEventListener('click', () => navigateLightbox(1));

    // Close lightbox on background click
    elements.lightbox.addEventListener('click', (e) => {
        if (e.target === elements.lightbox) {
            closeLightbox();
        }
    });

    // Keyboard navigation
    document.addEventListener('keydown', (e) => {
        if (!elements.lightbox.classList.contains('active')) return;

        switch (e.key) {
            case 'Escape':
                closeLightbox();
                break;
            case 'ArrowLeft':
                navigateLightbox(-1);
                break;
            case 'ArrowRight':
                navigateLightbox(1);
                break;
        }
    });

    // Download button
    elements.downloadPeriodBtn.addEventListener('click', handleDownload);
}

// Handle download
function handleDownload() {
    // For now, link to GitHub releases
    const downloadUrl = `https://github.com/YOUR_USERNAME/hyperinflation-bank-note/releases`;

    // Check for local ZIP
    const localZip = `../assets/downloads/${periodData.id}.zip`;

    fetch(localZip, { method: 'HEAD' })
        .then(response => {
            if (response.ok) {
                const link = document.createElement('a');
                link.href = localZip;
                link.download = `${periodData.country}-hyperinflation-banknotes.zip`;
                link.click();
            } else {
                window.open(downloadUrl, '_blank');
            }
        })
        .catch(() => {
            window.open(downloadUrl, '_blank');
        });
}

// Show error
function showError(message) {
    document.querySelector('.detail-main').innerHTML = `
        <div class="container">
            <div class="error-message">
                <h2>Error</h2>
                <p>${message}</p>
                <a href="../index.html" class="btn btn-primary">Back to Collection</a>
            </div>
        </div>
    `;
}

// Export for use in HTML
window.initDetailPage = initDetailPage;
