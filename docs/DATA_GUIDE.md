# Data Management Guide

This guide explains how to add, modify, and manage data in the Hyperinflation Banknote Archive.

---

## Quick Reference

| Task | File(s) to Edit |
|------|-----------------|
| Add new period | `data/periods.json` |
| Edit period info | `data/periods.json` |
| Add exchange rate chart | `data/exchange-rates/{period-id}.json` |
| Add historical content | `content/{period-id}/info.md` |
| Add new banknote images | `assets/bills/originals/` then run script |
| Regenerate pages | `node scripts/generate-pages.js` |

---

## 1. Adding a New Hyperinflation Period

### Step 1: Edit `data/periods.json`

Add a new entry to the `periods` array:

```json
{
  "id": "country-startyear-endyear",
  "country": "Country Name",
  "countryCode": "XX",
  "currency": "Currency Name",
  "currencySymbol": "$",
  "periodStart": "1990",
  "periodEnd": "1995",
  "peakInflation": "1,000% monthly",
  "peakMonth": "January 1994",
  "exchangeRatePeak": "1 million per USD",
  "cause": "Brief cause description",
  "resolution": "How it ended",
  "bills": [
    "filename1.png",
    "filename2.png"
  ],
  "featured": false
}
```

### Field Reference

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| `id` | Yes | Unique identifier (lowercase, hyphens) | `"germany-1921-1923"` |
| `country` | Yes | Display name | `"Germany"` |
| `countryCode` | Yes | ISO 3166-1 alpha-2 code (for flag) | `"DE"` |
| `currency` | Yes | Currency name | `"Papiermark"` |
| `currencySymbol` | No | Currency symbol | `"ℳ"` |
| `periodStart` | Yes | Start year | `"1921"` |
| `periodEnd` | Yes | End year or "present" | `"1923"` |
| `peakInflation` | Yes | Peak inflation rate | `"29,500% monthly"` |
| `peakMonth` | Yes | Month of peak | `"October 1923"` |
| `exchangeRatePeak` | Yes | Exchange rate at peak | `"4.2 trillion marks per USD"` |
| `cause` | Yes | Brief cause | `"War reparations, money printing"` |
| `resolution` | Yes | How it ended | `"Introduction of Rentenmark"` |
| `bills` | Yes | Array of image filenames | `["100_billion_mark.png"]` |
| `featured` | No | Show in featured section | `true` or `false` |

### Country Codes

Find codes at: https://flagcdn.com/en/codes.json

Common ones:
- Germany: `DE`, Austria: `AT`, Hungary: `HU`
- Zimbabwe: `ZW`, Venezuela: `VE`, Argentina: `AR`
- Brazil: `BR`, Russia: `RU`, Poland: `PL`

### Step 2: Add Banknote Images

1. Place original images in `assets/bills/originals/`
2. Run the image processor:
   ```bash
   python scripts/process-images.py
   ```
3. This creates web and thumbnail versions automatically

### Step 3: Generate the Detail Page

```bash
node scripts/generate-pages.js
```

This creates `pages/{period-id}.html` and `content/{period-id}/info.md`

### Step 4: Edit Historical Content

Edit `content/{period-id}/info.md` with detailed information (see Section 3).

---

## 2. Adding Exchange Rate Data (for Charts)

Create a file: `data/exchange-rates/{period-id}.json`

### Template

```json
{
  "periodId": "germany-1921-1923",
  "currency": "Papiermark",
  "baseCurrency": "USD",
  "unit": "Marks per 1 USD",
  "useLogScale": true,
  "sources": [
    "Source Name 1",
    "Source Name 2"
  ],
  "dataPoints": [
    { "date": "1921-01", "rate": 64 },
    { "date": "1921-06", "rate": 70 },
    { "date": "1922-01", "rate": 192 },
    { "date": "1922-06", "rate": 317 },
    { "date": "1923-01", "rate": 17792 },
    { "date": "1923-06", "rate": 109966 },
    { "date": "1923-11", "rate": 4200000000000 }
  ]
}
```

### Field Reference

| Field | Description |
|-------|-------------|
| `periodId` | Must match the period's `id` in periods.json |
| `currency` | Local currency name |
| `baseCurrency` | Usually `"USD"` |
| `unit` | Label for Y-axis |
| `useLogScale` | `true` for hyperinflation (always recommended) |
| `sources` | Array of source citations |
| `dataPoints` | Array of {date, rate} objects |

### Date Format

Use `YYYY-MM` format: `"1923-11"` for November 1923

### Tips for Finding Data

1. **Academic sources**: NBER, IMF historical data
2. **Wikipedia**: Often has tables with exchange rates
3. **Central bank archives**: Historical statistics
4. **Books**: "When Money Dies" (Germany), various economic histories

---

## 3. Writing Historical Content (Markdown)

Edit `content/{period-id}/info.md`

### Template Structure

```markdown
# {Country} Hyperinflation ({Start}-{End})

## Overview

Brief 2-3 sentence summary of what happened.

## Causes

### Primary Cause 1
Explanation...

### Primary Cause 2
Explanation...

## Timeline

- **{Year}**: Event 1
- **{Year}**: Event 2
- **{Year}**: Peak reached

## Life During Hyperinflation

### Daily Impact
- Bullet points about daily life
- How people coped
- Social effects

### Economic Effects
Description of economic collapse...

## Resolution

How the hyperinflation ended...

## Legacy

Long-term effects...

## Key Statistics

| Metric | Value |
|--------|-------|
| Duration | X years |
| Peak monthly inflation | X% |
| Exchange rate peak | X per USD |

## Sources

- Source 1
- Source 2
```

### Markdown Tips

- Use `**bold**` for emphasis
- Use `- ` for bullet lists
- Use `| table | format |` for tables
- Use `###` for subsections
- Keep paragraphs short for readability

---

## 4. Adding New Banknote Images

### Image Requirements

| Aspect | Recommendation |
|--------|----------------|
| Format | PNG or JPG |
| Resolution | At least 1500px wide |
| Quality | High quality scans preferred |
| Naming | Descriptive: `100_billion_mark.png` |

### Naming Convention

```
{denomination}_{unit}_{currency}.png
```

Examples:
- `100_billion_mark.png`
- `1_million_Intis.png`
- `50_Trillions_ZWR.png`

Special prefixes (optional):
- `F2-1 ` prefix for sequential ordering

### Process

1. Add images to `assets/bills/originals/`
2. Run: `python scripts/process-images.py`
3. Update `bills` array in `data/periods.json`
4. Regenerate pages: `node scripts/generate-pages.js`

---

## 5. Modifying Existing Data

### Change Period Information

1. Edit `data/periods.json`
2. Run `node scripts/generate-pages.js` (regenerates all pages)

### Update Historical Content

Just edit `content/{period-id}/info.md` - changes are live immediately

### Update Exchange Rate Data

Edit `data/exchange-rates/{period-id}.json` - changes are live immediately

### Replace an Image

1. Replace file in `assets/bills/originals/`
2. Run `python scripts/process-images.py`
3. Clear browser cache to see changes

---

## 6. File Locations Summary

```
data/
├── periods.json              # Master list of all periods
└── exchange-rates/
    ├── germany-1921-1923.json
    ├── zimbabwe-2007-2009.json
    └── {period-id}.json      # One file per period

content/
├── germany-1921-1923/
│   └── info.md               # Historical content
├── zimbabwe-2007-2009/
│   └── info.md
└── {period-id}/
    └── info.md               # One folder per period

assets/bills/
├── originals/                # Full resolution (for downloads)
├── web/                      # 1200px wide (auto-generated)
└── thumbnails/               # 300px wide (auto-generated)

pages/
├── germany-1921-1923.html    # Auto-generated detail pages
└── {period-id}.html
```

---

## 7. Scripts Reference

### `scripts/process-images.py`

Processes original images into web and thumbnail versions.

```bash
python scripts/process-images.py
```

- Input: `assets/bills/originals/*.png`
- Output: `assets/bills/web/*.jpg` and `assets/bills/thumbnails/*.jpg`
- Compression: ~94% size reduction

### `scripts/generate-pages.js`

Generates HTML detail pages for all periods.

```bash
node scripts/generate-pages.js
```

- Reads: `data/periods.json` and `pages/template.html`
- Creates: `pages/{period-id}.html` for each period
- Creates: `content/{period-id}/info.md` placeholder if missing

---

## 8. Common Tasks Checklist

### Adding a Complete New Period

- [ ] Add entry to `data/periods.json`
- [ ] Add original images to `assets/bills/originals/`
- [ ] Run `python scripts/process-images.py`
- [ ] Run `node scripts/generate-pages.js`
- [ ] Edit `content/{period-id}/info.md`
- [ ] Create `data/exchange-rates/{period-id}.json` (optional)
- [ ] Test locally with `npx serve .`

### Updating Content Only

- [ ] Edit `content/{period-id}/info.md`
- [ ] Refresh browser

### Fixing a Typo in Period Data

- [ ] Edit `data/periods.json`
- [ ] Run `node scripts/generate-pages.js`

---

## 9. Data Status Tracker

### Periods with Complete Data

| Period | periods.json | Exchange Rate | Content |
|--------|--------------|---------------|---------|
| germany-1921-1923 | ✅ | ✅ | ✅ |
| austria-1921-1922 | ✅ | ❌ | Placeholder |
| hungary-1945-1946 | ✅ | ❌ | Placeholder |
| zimbabwe-2007-2009 | ✅ | ❌ | Placeholder |
| ... | ... | ... | ... |

Update this table as you add data!

---

## 10. Useful Resources for Research

### Exchange Rate Data

- [MeasuringWorth.com](https://www.measuringworth.com/) - Historical exchange rates
- [FRED Economic Data](https://fred.stlouisfed.org/) - Federal Reserve data
- [IMF Data](https://data.imf.org/) - International monetary data
- Wikipedia tables (often well-sourced)

### Historical Context

- "When Money Dies" by Adam Fergusson (Germany)
- "The Big Reset" by Willem Middelkoop
- Central bank historical publications
- Academic papers (Google Scholar)

### Country Codes & Flags

- [ISO Country Codes](https://www.iso.org/iso-3166-country-codes.html)
- [FlagCDN](https://flagcdn.com/) - Free flag images (used in project)
