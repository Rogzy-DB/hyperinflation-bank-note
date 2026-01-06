# Hyperinflation Banknote Archive

A web-based visualization platform for historical hyperinflation banknotes, organized by country and period, featuring exchange rate charts, downloadable databases, and detailed historical context.

## Live Demo

Visit the live site: [https://decouvreBitcoin.github.io/hyperinflation-bank-note](https://decouvreBitcoin.github.io/hyperinflation-bank-note)

## Features

- **19 Hyperinflation Periods** from around the world
- **44 High-Quality Banknote Images** with zoom capability
- **Exchange Rate Charts** showing currency collapse over time
- **Historical Context** for each period in Markdown format
- **Download Options** - Full collection or per-period ZIPs
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Dark Theme** - Easy on the eyes

## Periods Covered

| Country | Period | Currency | Peak Inflation |
|---------|--------|----------|----------------|
| Germany | 1921-1923 | Papiermark | 29,500% monthly |
| Hungary | 1945-1946 | Pengő | 41.9 quadrillion % |
| Zimbabwe | 2007-2009 | ZWD/ZWN/ZWR | 79.6 billion % |
| Venezuela | 2016-2021 | Bolívar | 1,000,000%+ |
| Yugoslavia | 1992-1994 | Dinar | 313 million % |
| Greece | 1941-1944 | Drachma | 8.55 billion % |
| And 13 more... | | | |

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
│   ├── periods.json        # All periods metadata
│   └── exchange-rates/     # Chart data per period
├── content/
│   └── {period-id}/        # Markdown info per period
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
    └── generate-pages.js   # Page generation
```

## Development

### Prerequisites

- Python 3.x with Pillow (`pip install Pillow`)
- Node.js 18+ (optional, for npm scripts)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/decouvreBitcoin/hyperinflation-bank-note.git
   cd hyperinflation-bank-note
   ```

2. Extract banknote images (if not already done):
   ```bash
   unzip "Hyperinflation Bills.zip" -d assets/bills/originals/
   ```

3. Process images (create thumbnails and web versions):
   ```bash
   python scripts/process-images.py
   ```

4. Generate detail pages:
   ```bash
   node scripts/generate-pages.js
   ```

5. Serve locally:
   ```bash
   npx serve .
   # or use any local server like Live Server in VS Code
   ```

### Adding New Periods

1. Add period data to `data/periods.json`
2. Add bill images to `assets/bills/originals/`
3. Run `python scripts/process-images.py`
4. Run `node scripts/generate-pages.js`
5. Edit `content/{period-id}/info.md` with historical context
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

- Banknote images: Personal collection (educational use)
- Exchange rate data: Various historical sources
- Historical information: Academic sources and archives

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

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

- DecouvreBitcoin for the initial collection
- All the historians and economists who documented these events
