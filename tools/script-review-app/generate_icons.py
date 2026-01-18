"""Generate PWA icons from SVG using Pillow"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Paths
icons_dir = Path(__file__).parent / "frontend" / "static" / "icons"

# Create simple microphone icon
def create_icon(size):
    # Create image with dark background
    img = Image.new('RGB', (size, size), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Draw microphone emoji representation (simplified circle)
    center = size // 2
    radius = int(size * 0.3)
    
    # Blue circle (representing microphone)
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        fill='#3b82f6',
        outline='#60a5fa',
        width=int(size * 0.02)
    )
    
    # Mic stand (rectangle)
    stand_width = int(size * 0.05)
    stand_height = int(size * 0.2)
    draw.rectangle(
        [center - stand_width//2, center + radius, center + stand_width//2, center + radius + stand_height],
        fill='#3b82f6'
    )
    
    return img

# Generate 192x192 PNG
icon_192 = create_icon(192)
icon_192.save(icons_dir / "icon-192.png")
print("✅ Created icon-192.png")

# Generate 512x512 PNG
icon_512 = create_icon(512)
icon_512.save(icons_dir / "icon-512.png")
print("✅ Created icon-512.png")

print(f"\n✅ PWA icons generated in {icons_dir}")
