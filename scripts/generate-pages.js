/**
 * Generate Detail Pages Script
 *
 * This script generates individual HTML pages for each hyperinflation period
 * based on the template and periods.json data.
 *
 * Usage:
 *   node scripts/generate-pages.js
 */

const fs = require('fs');
const path = require('path');

// Paths
const TEMPLATE_PATH = path.join(__dirname, '..', 'pages', 'template.html');
const PERIODS_PATH = path.join(__dirname, '..', 'data', 'periods.json');
const OUTPUT_DIR = path.join(__dirname, '..', 'pages');
const CONTENT_DIR = path.join(__dirname, '..', 'content');

// Read template
function readTemplate() {
    return fs.readFileSync(TEMPLATE_PATH, 'utf8');
}

// Read periods data
function readPeriodsData() {
    const data = fs.readFileSync(PERIODS_PATH, 'utf8');
    return JSON.parse(data).periods;
}

// Generate page for a single period
function generatePage(template, period) {
    let html = template;

    // Replace placeholders
    html = html.replace(/\{\{COUNTRY\}\}/g, period.country);
    // Turkey is a contrast case (chronic inflation), never called a hyperinflation
    const kind = period.kind === 'chronic' ? 'Chronic Inflation' : 'Hyperinflation';
    html = html.replace(/\{\{KIND\}\}/g, kind);
    html = html.replace(/\{\{KIND_LC\}\}/g, kind.toLowerCase());
    html = html.replace(/\{\{PERIOD\}\}/g, `${period.periodStart}–${period.periodEnd}`);
    html = html.replace(/\{\{CURRENCY\}\}/g, period.currency);
    html = html.replace(/\{\{ID\}\}/g, period.id);
    // Flag: only when the country has one today (Soviet Russia has none on the flag CDN)
    const flag = period.countryCode
        ? `<img id="countryFlag" src="https://flagcdn.com/w160/${period.countryCode.toLowerCase()}.png" alt="${period.country} flag" width="80" height="60">`
        : '';
    html = html.replace(/\{\{FLAG_IMG\}\}/g, flag);
    // Open Graph image: the period's first banknote, web size
    const ogBill = (period.bills && period.bills[0]) || 'TizMillio_B_Pengo.png'; // a period with no note shares the site's image
    html = html.replace(/\{\{OG_IMAGE\}\}/g, encodeURI(`assets/bills/web/${ogBill.replace('.png', '.jpg')}`));

    return html;
}

// The history texts (content/<id>/info.md) are NOT generated here: they are exported from the
// sourced knowledge base by scripts/export-knowledge.py. A missing one is reported, never stubbed.
function checkContent(periodId) {
    if (!fs.existsSync(path.join(CONTENT_DIR, periodId, 'info.md'))) {
        console.log(`  ⚠ missing: content/${periodId}/info.md (run scripts/export-knowledge.py)`);
    }
}

// Main function
function main() {
    console.log('╔════════════════════════════════════════════════════════╗');
    console.log('║  Generating Detail Pages                               ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');

    const template = readTemplate();
    const periods = readPeriodsData();

    console.log(`Found ${periods.length} periods\n`);

    let created = 0;
    let skipped = 0;

    periods.forEach(period => {
        const outputPath = path.join(OUTPUT_DIR, `${period.id}.html`);

        // Always regenerate pages
        const html = generatePage(template, period);
        fs.writeFileSync(outputPath, html);
        console.log(`✓ Generated: pages/${period.id}.html`);
        created++;

        checkContent(period.id);
    });

    console.log('\n─'.repeat(50));
    console.log(`\n✅ Done! Generated ${created} pages.`);

    // List content directories that need info.md updates
    console.log('\n📝 Content files created (edit these for historical info):');
    periods.forEach(period => {
        console.log(`   content/${period.id}/info.md`);
    });
}

main();
