# Hyperinflation Banknote Visualizer - Project Roadmap

## Project Overview
A web-based visualization platform for historical hyperinflation banknotes, organized by country and period, featuring exchange rate charts, downloadable databases, and detailed historical context.

---

## Phase 1: Foundation (MVP)

### 1.1 Project Structure
```
hyperinflation-bank-note/
├── index.html                    # Main landing page with all periods
├── css/
│   └── style.css                 # Global styles
├── js/
│   ├── main.js                   # Main app logic
│   ├── charts.js                 # Chart.js integration
│   └── download.js               # Download functionality
├── data/
│   ├── periods.json              # All hyperinflation periods metadata
│   └── exchange-rates/           # Exchange rate data per period
│       └── {country-period}.json
├── content/
│   └── {country-period}/         # Per-period content
│       └── info.md               # Historical context markdown
├── assets/
│   ├── flags/                    # Country flag images
│   ├── bills/
│   │   ├── originals/            # Full resolution (for download)
│   │   ├── web/                  # Optimized for display (~1200px)
│   │   └── thumbnails/           # Small previews (~300px)
│   └── downloads/                # Pre-built ZIP files
├── pages/
│   └── {country-period}.html     # Detail page per period
├── scripts/
│   └── process-images.js         # Image optimization script
└── README.md
```

### 1.2 Data Schema

**periods.json** - Master data file:
```json
{
  "periods": [
    {
      "id": "germany-1921-1923",
      "country": "Germany",
      "countryCode": "DE",
      "currency": "Papiermark",
      "periodStart": "1921",
      "periodEnd": "1923",
      "peakInflation": "29,500%",
      "peakMonth": "October 1923",
      "exchangeRatePeak": "4.2 trillion marks per USD",
      "billCount": 8,
      "thumbnail": "assets/bills/thumbnails/100_billion_mark.png",
      "featured": true
    }
  ]
}
```

**Exchange rate data** (per period):
```json
{
  "periodId": "germany-1921-1923",
  "currency": "Papiermark",
  "baseCurrency": "USD",
  "dataPoints": [
    { "date": "1921-01", "rate": 75 },
    { "date": "1923-11", "rate": 4200000000000 }
  ],
  "useLogScale": true
}
```

---

## Phase 2: Core Features

### 2.1 Index Page (Landing)
- Grid of cards, each representing a hyperinflation period
- Card displays: Country flag, period dates, peak inflation rate, bill thumbnail
- Filter/sort by: Country, decade, severity
- Search functionality
- "Download All" button

### 2.2 Detail Pages
- Full bill gallery with lightbox
- Exchange rate chart (Chart.js, logarithmic scale)
- Historical context (rendered from Markdown)
- Key statistics panel
- Download buttons (this period only)
- Navigation back to index

### 2.3 Image Processing
- Node.js script to generate:
  - Thumbnails (300px width, ~50KB)
  - Web versions (1200px width, ~200KB)
  - Keep originals for download (2-8MB each)

---

## Phase 3: Data Population

### Identified Hyperinflation Periods (from your bills)

| ID | Country | Period | Currency | Bills Found |
|----|---------|--------|----------|-------------|
| germany-1921-1923 | Germany | 1921-1923 | Papiermark | 10k, 100k, 1B, 10B, 100B, 500M mark |
| austria-1921-1922 | Austria | 1921-1922 | Krone | 1000, 10000 Kronen |
| hungary-1945-1946 | Hungary | 1945-1946 | Pengő | MilPengő, B-Pengő, TizMillió |
| zimbabwe-2006-2009 | Zimbabwe | 2006-2009 | ZWD/ZWN/ZWR | Multiple eras of dollars |
| greece-1941-1944 | Greece | 1941-1944 | Drachma | 100M, 500M, 2000M drachma |
| yugoslavia-1992-1994 | Yugoslavia | 1992-1994 | Dinar | 5B, 50B dinar |
| brazil-1986-1994 | Brazil | 1986-1994 | Cruzado/Cruzeiro | 1000 Cruzados |
| peru-1988-1990 | Peru | 1988-1990 | Inti | 1M Intis |
| argentina-1989-1990 | Argentina | 1989-1990 | Austral | 10k Australes, 500k pesos |
| nicaragua-1987-1990 | Nicaragua | 1987-1990 | Córdoba | 200k Nicaragua |
| zaire-1991-1994 | Zaire | 1991-1994 | Zaïre | 100k, 500k Zaire |
| russia-1992-1994 | Russia | 1992-1994 | Ruble | 1000, 50000 Rouble |
| poland-1989-1990 | Poland | 1989-1990 | Złoty | 10k Zlotych |
| georgia-1993-1994 | Georgia | 1993-1994 | Coupon | 1M Georgia |
| turkey-1990s-2005 | Turkey | 1990s-2005 | Lira | 1M Lira |
| venezuela-2016-2021 | Venezuela | 2016-2021 | Bolívar | 1M Bolivar |
| angola-1991-1999 | Angola | 1991-1999 | Kwanza | 500 Angola |
| lebanon-2019-present | Lebanon | 2019-present | Pound | 10k Liban |
| japan-occupation | Philippines | 1942-1945 | Fiat Peso | 10 centavos |

---

## Phase 4: Enhancements

### 4.1 UX Improvements
- Lazy loading for images
- Smooth page transitions
- Mobile-responsive design
- Dark/light mode toggle
- Progress indicators for downloads

### 4.2 Educational Content
- Timeline view of all periods
- Comparison charts between periods
- "Worst hyperinflations" ranking
- Currency conversion calculator (historical)

---

## Phase 5: Future (React/TypeScript V2)
- Migrate to React + TypeScript
- Add state management
- Implement virtual scrolling for large collections
- Add user contributions system
- Multi-language support

---

## GitHub Pages Considerations

### Storage Limits
- GitHub Pages: 1GB repo limit, 100MB file limit
- Original images (~144MB) should use Git LFS or external hosting
- Web-optimized images should be under 500MB total

### Recommended Approach
1. Store optimized images in repo (web + thumbnails)
2. Host original images on:
   - GitHub Releases (for download ZIPs)
   - Or external CDN (Cloudflare R2, Backblaze B2)

---

## Immediate Next Steps

1. **Extract and organize bills** from ZIP into category folders
2. **Create image processing script** (Node.js + Sharp)
3. **Build base HTML/CSS structure**
4. **Create periods.json** with identified periods
5. **Build first detail page** as template
6. **Research and add exchange rate data**
7. **Write historical content** for each period

---

## Tech Stack Summary

| Component | Technology |
|-----------|------------|
| Frontend | HTML5, CSS3, Vanilla JS |
| Charts | Chart.js 4.x |
| Markdown | Marked.js |
| Image Processing | Node.js + Sharp |
| Hosting | GitHub Pages |
| Downloads | GitHub Releases (for large ZIPs) |
| Future V2 | React + TypeScript |
