# Hyperinflation Archive

A web-based visualization platform for historical hyperinflation banknotes, organized by country and period, with exchange-rate charts and a sourced history of each period.

## Live Demo

Visit the live site: [https://hyperinflation.rogzy.org](https://hyperinflation.rogzy.org)

## Features

- **20 hyperinflations** and one contrast case (Turkey 1990–2005, chronic inflation that never reached 50% a month)
- **44 banknotes** with zoom, each labelled with its denomination and date
- **Exchange-rate charts** on a true time axis, with their unit and caveats shown
- **A sourced history** for each period
- **Downloads**: the full collection or one ZIP per period
- Works on desktop, tablet and phone

## The periods, by worst month

"Worst month" is the highest monthly inflation (Hanke & Krus, *World Hyperinflations*, Cato Working
Paper no. 8, 2012, unless noted). A hyperinflation starts when prices rise 50% or more in a month.

| Country | Period | Currency | Worst month | When |
|---------|--------|----------|-------------|------|
| Hungary | 1945–1946 | Pengő | 41.9 quadrillion % | July 1946 |
| Zimbabwe | 2007–2009 | Zimbabwean Dollar | 79.6 billion % | mid-November 2008 |
| Yugoslavia | 1992–1994 | Dinar | 313 million % | January 1994 |
| Germany | 1921–1923 | Papiermark | 29,500% | October 1923 |
| Greece | 1941–1945 | Drachma | 13,800% | October 1944 |
| Peru | 1988–1990 | Inti | 397% | August 1990 |
| Nicaragua | 1986–1991 | Córdoba | 261% | March 1991 |
| Zaire | 1991–1994 | Zaïre | 250% | November 1993 |
| Russia | 1992–1994 | Ruble | 245% | January 1992 |
| Soviet Russia | 1921–1924 | Paper ruble (sovznak) | 212% | February 1924 |
| Georgia | 1993–1994 | Kuponi | 211% | September 1994 |
| Argentina | 1989–1990 | Austral | 197% | July 1989 |
| Venezuela | 2016–2022 | Bolívar | 192% | January 2019 |
| Bolivia | 1984–1985 | Peso boliviano | 183% | February 1985 |
| Austria | 1921–1922 | Krone | 129% | August 1922 |
| Angola | 1991–1999 | Kwanza | 84.1% | May 1996 |
| Brazil | 1986–1994 | Cruzado / Cruzeiro | 82.4% | March 1990 |
| Poland | 1989–1990 | Złoty | 77.3% | January 1990 |
| Philippines | 1942–1945 | Japanese Occupation Peso | 60% | January 1944 |
| Lebanon | 2019–2023 | Lebanese Pound | 52.6% (implied) | July 2020 |
| Turkey | 1990–2005 | Lira | never ≥ 50% | — (contrast case) |

Venezuela: National Assembly estimate. Lebanon: Hanke's implied rate from the parallel exchange rate.

## Project Structure

```
hyperinflation-bank-note/
├── index.html              # Main landing page
├── css/
│   ├── style.css           # Global styles
│   └── detail.css          # Detail page styles
├── js/
│   ├── main.js             # Index page logic
│   └── detail.js           # Detail page logic
├── data/
│   ├── periods.json        # All periods metadata (figures, banknote labels)
│   ├── exchange-rates/     # Chart data per period
│   └── books/              # Related books per period
├── content/
│   └── {period-id}/        # History per period (exported, see below)
│       └── info.md
├── assets/
│   └── bills/
│       ├── originals/      # Full resolution images
│       ├── web/            # Optimized (1200px)
│       └── thumbnails/     # Small previews (300px)
├── pages/
│   └── {period-id}.html    # Detail pages
└── scripts/
    ├── process-images.py   # Image optimization
    ├── generate-pages.js   # Page generation
    └── export-knowledge.py # Histories from the sourced knowledge base
```

## Development

### Prerequisites

- Python 3.x with Pillow (`pip install Pillow`)
- Node.js 18+ (optional, for npm scripts)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Rogzy-DB/hyperinflation-bank-note.git
   cd hyperinflation-bank-note
   ```

2. Process images (create thumbnails and web versions):
   ```bash
   python3 scripts/process-images.py
   ```

3. Generate detail pages:
   ```bash
   node scripts/generate-pages.js
   ```

4. Serve locally:
   ```bash
   npx serve .
   # or use any local server like Live Server in VS Code
   ```

### Adding New Periods

1. Add period data to `data/periods.json`
2. Add bill images to `assets/bills/originals/`
3. Run `python scripts/process-images.py`
4. Run `node scripts/generate-pages.js`
5. Write the history in the knowledge base and export it (`python3 scripts/export-knowledge.py <dir>`):
   `content/*/info.md` is generated, never edited by hand. Every figure carries its source; anything
   marked ⚠ (unverified) is left out of the export.
6. (Optional) Add exchange rate data to `data/exchange-rates/{period-id}.json`

**See [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md) for detailed instructions and templates.**

Quick reference: [docs/CHEATSHEET.md](docs/CHEATSHEET.md)

## Documentation

| Document | Description |
|----------|-------------|
| [ROADMAP.md](ROADMAP.md) | Project roadmap and future plans |
| [docs/DATA_GUIDE.md](docs/DATA_GUIDE.md) | Complete guide for managing data |
| [docs/CHEATSHEET.md](docs/CHEATSHEET.md) | Quick command reference |

## Data Sources

- Banknote images: David St-Onge's collection, used with his permission. **Not covered by the MIT licence.**
- Monthly peaks and episode dates: Hanke & Krus (2012), *World Hyperinflations*, Cato Working Paper no. 8.
- Histories: cited per period (Hanke & Krus, Wikipedia articles, academic papers named in each text).
- Exchange-rate charts: the sources and caveats are shown under each chart; several series are approximate
  and say so. Angola and the Philippines have no chart until a sourced series exists.
- Book covers: Open Library. Flags: flagcdn.

## Tech Stack

- Pure HTML5, CSS3, JavaScript (no frameworks)
- Chart.js for exchange rate visualization
- Marked.js for Markdown rendering
- Pillow (Python) for image processing

## Future Plans (V2)

- [ ] React + TypeScript migration
- [ ] Timeline view of all hyperinflations
- [ ] Comparison charts between periods
- [ ] User contributions system
- [ ] Multi-language support

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

Code: MIT License, see [LICENSE](LICENSE). The banknote images are not covered by it.

## Acknowledgments

- David St-Onge and DecouvreBitcoin for the banknote collection
- All the historians and economists who documented these events
