# Quick Cheatsheet

## Most Common Tasks

### Add new banknote images
```bash
# 1. Put images in originals folder
cp your-images/*.png assets/bills/originals/

# 2. Process images (creates web + thumbnails)
python scripts/process-images.py

# 3. Add filenames to data/periods.json in the "bills" array
```

### Add new period
```bash
# 1. Edit data/periods.json - add new entry
# 2. Add images as above
# 3. Generate detail page
node scripts/generate-pages.js

# 4. Edit the content file
code content/{period-id}/info.md
```

### Add exchange rate chart
```bash
# Create file: data/exchange-rates/{period-id}.json
# Use template from docs/DATA_GUIDE.md
```

### Test locally
```bash
npx serve .
# Open http://localhost:3000
```

### Regenerate all pages
```bash
node scripts/generate-pages.js
```

---

## Key Files

| What | Where |
|------|-------|
| All periods data | `data/periods.json` |
| Chart data | `data/exchange-rates/{id}.json` |
| Historical text | `content/{id}/info.md` |
| Original images | `assets/bills/originals/` |
| Page template | `pages/template.html` |

---

## Period ID Format

```
{country}-{start-year}-{end-year}
```

Examples:
- `germany-1921-1923`
- `zimbabwe-2007-2009`
- `lebanon-2019-present`

---

## Country Codes (for flags)

| Country | Code |
|---------|------|
| Germany | DE |
| Austria | AT |
| Hungary | HU |
| Zimbabwe | ZW |
| Greece | GR |
| Yugoslavia/Serbia | RS |
| Brazil | BR |
| Peru | PE |
| Argentina | AR |
| Nicaragua | NI |
| Zaire/Congo | CD |
| Russia | RU |
| Poland | PL |
| Georgia | GE |
| Turkey | TR |
| Venezuela | VE |
| Angola | AO |
| Lebanon | LB |
| Philippines | PH |

Full list: https://flagcdn.com/en/codes.json
