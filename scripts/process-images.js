/**
 * Image Processing Script for Hyperinflation Banknote Visualizer
 *
 * This script processes original banknote images to create:
 * - Web-optimized versions (1200px width, ~200KB)
 * - Thumbnails (300px width, ~50KB)
 *
 * Requirements:
 *   npm install sharp
 *
 * Usage:
 *   node scripts/process-images.js
 */

const fs = require('fs');
const path = require('path');

// Check if sharp is installed
let sharp;
try {
    sharp = require('sharp');
} catch (e) {
    console.error('Sharp is not installed. Please run: npm install sharp');
    console.log('\nAlternatively, you can use the Python script: python scripts/process-images.py');
    process.exit(1);
}

// Configuration
const CONFIG = {
    inputDir: path.join(__dirname, '..', 'assets', 'bills', 'originals'),
    webDir: path.join(__dirname, '..', 'assets', 'bills', 'web'),
    thumbDir: path.join(__dirname, '..', 'assets', 'bills', 'thumbnails'),
    webWidth: 1200,      // Width for web display
    thumbWidth: 300,     // Width for thumbnails
    webQuality: 85,      // JPEG quality for web (0-100)
    thumbQuality: 80,    // JPEG quality for thumbnails
    format: 'jpeg',      // Output format (jpeg for smaller size)
    supportedFormats: ['.png', '.jpg', '.jpeg', '.webp', '.tiff']
};

// Ensure output directories exist
function ensureDirectories() {
    [CONFIG.webDir, CONFIG.thumbDir].forEach(dir => {
        if (!fs.existsSync(dir)) {
            fs.mkdirSync(dir, { recursive: true });
            console.log(`Created directory: ${dir}`);
        }
    });
}

// Get all image files from input directory
function getImageFiles() {
    if (!fs.existsSync(CONFIG.inputDir)) {
        console.error(`Input directory does not exist: ${CONFIG.inputDir}`);
        console.log('\nPlease extract the banknote images to: assets/bills/originals/');
        return [];
    }

    return fs.readdirSync(CONFIG.inputDir)
        .filter(file => {
            const ext = path.extname(file).toLowerCase();
            return CONFIG.supportedFormats.includes(ext);
        });
}

// Process a single image
async function processImage(filename) {
    const inputPath = path.join(CONFIG.inputDir, filename);
    const baseName = path.parse(filename).name;

    // Output paths (always JPEG for smaller files)
    const webPath = path.join(CONFIG.webDir, `${baseName}.jpg`);
    const thumbPath = path.join(CONFIG.thumbDir, `${baseName}.jpg`);

    try {
        const image = sharp(inputPath);
        const metadata = await image.metadata();

        console.log(`Processing: ${filename} (${metadata.width}x${metadata.height})`);

        // Create web version
        await sharp(inputPath)
            .resize(CONFIG.webWidth, null, {
                withoutEnlargement: true,
                fit: 'inside'
            })
            .jpeg({ quality: CONFIG.webQuality, progressive: true })
            .toFile(webPath);

        // Create thumbnail
        await sharp(inputPath)
            .resize(CONFIG.thumbWidth, null, {
                withoutEnlargement: true,
                fit: 'inside'
            })
            .jpeg({ quality: CONFIG.thumbQuality })
            .toFile(thumbPath);

        // Get output file sizes
        const webStats = fs.statSync(webPath);
        const thumbStats = fs.statSync(thumbPath);
        const originalStats = fs.statSync(inputPath);

        console.log(`  ✓ Web: ${(webStats.size / 1024).toFixed(0)}KB`);
        console.log(`  ✓ Thumb: ${(thumbStats.size / 1024).toFixed(0)}KB`);
        console.log(`  ✓ Original: ${(originalStats.size / 1024 / 1024).toFixed(1)}MB`);

        return {
            filename,
            success: true,
            originalSize: originalStats.size,
            webSize: webStats.size,
            thumbSize: thumbStats.size
        };

    } catch (error) {
        console.error(`  ✗ Error processing ${filename}: ${error.message}`);
        return {
            filename,
            success: false,
            error: error.message
        };
    }
}

// Main function
async function main() {
    console.log('╔════════════════════════════════════════════════════════╗');
    console.log('║  Hyperinflation Banknote Image Processor               ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');

    ensureDirectories();

    const images = getImageFiles();

    if (images.length === 0) {
        console.log('No images found to process.');
        return;
    }

    console.log(`Found ${images.length} images to process\n`);
    console.log('─'.repeat(50));

    const results = [];
    for (const image of images) {
        const result = await processImage(image);
        results.push(result);
        console.log('');
    }

    // Summary
    console.log('─'.repeat(50));
    console.log('\n📊 Summary:');

    const successful = results.filter(r => r.success);
    const failed = results.filter(r => !r.success);

    console.log(`  ✓ Processed: ${successful.length}/${images.length}`);

    if (successful.length > 0) {
        const totalOriginal = successful.reduce((sum, r) => sum + r.originalSize, 0);
        const totalWeb = successful.reduce((sum, r) => sum + r.webSize, 0);
        const totalThumb = successful.reduce((sum, r) => sum + r.thumbSize, 0);

        console.log(`\n  Original total: ${(totalOriginal / 1024 / 1024).toFixed(1)}MB`);
        console.log(`  Web total: ${(totalWeb / 1024 / 1024).toFixed(1)}MB (${((1 - totalWeb/totalOriginal) * 100).toFixed(0)}% reduction)`);
        console.log(`  Thumbnails total: ${(totalThumb / 1024 / 1024).toFixed(1)}MB`);
    }

    if (failed.length > 0) {
        console.log(`\n  ✗ Failed: ${failed.length}`);
        failed.forEach(r => console.log(`    - ${r.filename}: ${r.error}`));
    }

    console.log('\n✅ Done!');
}

main().catch(console.error);
