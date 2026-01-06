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
    html = html.replace(/\{\{PERIOD\}\}/g, `${period.periodStart}-${period.periodEnd}`);
    html = html.replace(/\{\{CURRENCY\}\}/g, period.currency);

    return html;
}

// Create content directory and placeholder info.md
function createContentDir(periodId, period) {
    const contentDir = path.join(CONTENT_DIR, periodId);

    if (!fs.existsSync(contentDir)) {
        fs.mkdirSync(contentDir, { recursive: true });
    }

    const infoPath = path.join(contentDir, 'info.md');

    // Only create if doesn't exist
    if (!fs.existsSync(infoPath)) {
        const placeholder = `# ${period.country} Hyperinflation (${period.periodStart}-${period.periodEnd})

## Overview

${period.country} experienced severe hyperinflation during the period of ${period.periodStart} to ${period.periodEnd}.
The ${period.currency} lost significant value, with peak monthly inflation reaching ${period.peakInflation}.

## Causes

${period.cause}

## Timeline

- **Start**: ${period.periodStart}
- **Peak**: ${period.peakMonth}
- **End**: ${period.periodEnd}

## Resolution

${period.resolution}

## Economic Impact

*[Additional historical details to be added]*

## Sources

*[Sources to be added]*
`;
        fs.writeFileSync(infoPath, placeholder);
        console.log(`  Created: content/${periodId}/info.md`);
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

        // Create content directory and placeholder
        createContentDir(period.id, period);
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
