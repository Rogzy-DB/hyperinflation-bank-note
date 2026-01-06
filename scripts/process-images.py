"""
Image Processing Script for Hyperinflation Banknote Visualizer

This script processes original banknote images to create:
- Web-optimized versions (1200px width, ~200KB)
- Thumbnails (300px width, ~50KB)

Requirements:
    pip install Pillow

Usage:
    python scripts/process-images.py
"""

import os
import sys
import io
from pathlib import Path

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    from PIL import Image
except ImportError:
    print("Pillow is not installed. Please run: pip install Pillow")
    sys.exit(1)

# Configuration
CONFIG = {
    'input_dir': Path(__file__).parent.parent / 'assets' / 'bills' / 'originals',
    'web_dir': Path(__file__).parent.parent / 'assets' / 'bills' / 'web',
    'thumb_dir': Path(__file__).parent.parent / 'assets' / 'bills' / 'thumbnails',
    'web_width': 1200,
    'thumb_width': 300,
    'web_quality': 85,
    'thumb_quality': 80,
    'supported_formats': {'.png', '.jpg', '.jpeg', '.webp', '.tiff', '.bmp'}
}


def ensure_directories():
    """Create output directories if they don't exist."""
    for dir_path in [CONFIG['web_dir'], CONFIG['thumb_dir']]:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory: {dir_path}")


def get_image_files():
    """Get all image files from input directory."""
    input_dir = CONFIG['input_dir']

    if not input_dir.exists():
        print(f"Input directory does not exist: {input_dir}")
        print("\nPlease extract the banknote images to: assets/bills/originals/")
        return []

    return [
        f for f in input_dir.iterdir()
        if f.is_file() and f.suffix.lower() in CONFIG['supported_formats']
    ]


def resize_image(img, max_width):
    """Resize image maintaining aspect ratio."""
    if img.width <= max_width:
        return img.copy()

    ratio = max_width / img.width
    new_height = int(img.height * ratio)
    return img.resize((max_width, new_height), Image.Resampling.LANCZOS)


def process_image(image_path):
    """Process a single image, creating web and thumbnail versions."""
    base_name = image_path.stem
    web_path = CONFIG['web_dir'] / f"{base_name}.jpg"
    thumb_path = CONFIG['thumb_dir'] / f"{base_name}.jpg"

    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for PNG with transparency)
            if img.mode in ('RGBA', 'P'):
                # Create white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            original_size = image_path.stat().st_size
            print(f"Processing: {image_path.name} ({img.width}x{img.height})")

            # Create web version
            web_img = resize_image(img, CONFIG['web_width'])
            web_img.save(web_path, 'JPEG', quality=CONFIG['web_quality'], progressive=True)

            # Create thumbnail
            thumb_img = resize_image(img, CONFIG['thumb_width'])
            thumb_img.save(thumb_path, 'JPEG', quality=CONFIG['thumb_quality'])

            # Get output sizes
            web_size = web_path.stat().st_size
            thumb_size = thumb_path.stat().st_size

            print(f"  ✓ Web: {web_size // 1024}KB")
            print(f"  ✓ Thumb: {thumb_size // 1024}KB")
            print(f"  ✓ Original: {original_size / 1024 / 1024:.1f}MB")

            return {
                'filename': image_path.name,
                'success': True,
                'original_size': original_size,
                'web_size': web_size,
                'thumb_size': thumb_size
            }

    except Exception as e:
        print(f"  ✗ Error processing {image_path.name}: {e}")
        return {
            'filename': image_path.name,
            'success': False,
            'error': str(e)
        }


def main():
    print("╔════════════════════════════════════════════════════════╗")
    print("║  Hyperinflation Banknote Image Processor (Python)      ║")
    print("╚════════════════════════════════════════════════════════╝\n")

    ensure_directories()

    images = get_image_files()

    if not images:
        print("No images found to process.")
        return

    print(f"Found {len(images)} images to process\n")
    print("─" * 50)

    results = []
    for image_path in sorted(images):
        result = process_image(image_path)
        results.append(result)
        print()

    # Summary
    print("─" * 50)
    print("\n📊 Summary:")

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"  ✓ Processed: {len(successful)}/{len(images)}")

    if successful:
        total_original = sum(r['original_size'] for r in successful)
        total_web = sum(r['web_size'] for r in successful)
        total_thumb = sum(r['thumb_size'] for r in successful)

        print(f"\n  Original total: {total_original / 1024 / 1024:.1f}MB")
        print(f"  Web total: {total_web / 1024 / 1024:.1f}MB ({(1 - total_web/total_original) * 100:.0f}% reduction)")
        print(f"  Thumbnails total: {total_thumb / 1024 / 1024:.1f}MB")

    if failed:
        print(f"\n  ✗ Failed: {len(failed)}")
        for r in failed:
            print(f"    - {r['filename']}: {r['error']}")

    print("\n✅ Done!")


if __name__ == "__main__":
    main()
