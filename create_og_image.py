from PIL import Image, ImageDraw, ImageFont
import os

# Create a 1200x630 image with blue gradient background
width, height = 1200, 630
image = Image.new('RGB', (width, height), '#4a90e2')

# Create gradient effect (simple two-color blend)
draw = ImageDraw.Draw(image)
for y in range(height):
    # Interpolate between #4a90e2 and #357abd
    ratio = y / height
    r = int(74 + (53 - 74) * ratio)
    g = int(144 + (122 - 144) * ratio)
    b = int(226 + (189 - 226) * ratio)
    draw.line([(0, y), (width, y)], fill=(r, g, b))

# Load and paste the logo
logo_path = 'docs/parieur_discipline.png'
if os.path.exists(logo_path):
    logo = Image.open(logo_path)
    # Resize logo to 250x250
    logo = logo.resize((250, 250), Image.Resampling.LANCZOS)

    # Create a white circle background for the logo
    circle = Image.new('RGBA', (260, 260), (255, 255, 255, 0))
    circle_draw = ImageDraw.Draw(circle)
    circle_draw.ellipse([0, 0, 260, 260], fill=(255, 255, 255, 255))

    # Paste white circle
    circle_pos = ((width - 260) // 2, 80)
    image.paste(circle, circle_pos, circle)

    # Paste logo on top
    logo_pos = ((width - 250) // 2, 85)
    if logo.mode == 'RGBA':
        image.paste(logo, logo_pos, logo)
    else:
        image.paste(logo, logo_pos)

# Add text
try:
    # Try to use system font
    title_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 72)
    subtitle_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 40)
except:
    # Fallback to default font
    title_font = ImageFont.load_default()
    subtitle_font = ImageFont.load_default()

# Draw title
title_text = "🎯 Parieur Discipliné"
title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
title_width = title_bbox[2] - title_bbox[0]
title_pos = ((width - title_width) // 2, 370)
draw.text(title_pos, title_text, fill='white', font=title_font)

# Draw subtitle
subtitle_text = "AI-Powered NHL & NBA Betting Predictions"
subtitle_bbox = draw.textbbox((0, 0), subtitle_text, font=subtitle_font)
subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
subtitle_pos = ((width - subtitle_width) // 2, 470)
draw.text(subtitle_pos, subtitle_text, fill='white', font=subtitle_font)

# Save
output_path = 'docs/og-preview.png'
image.save(output_path, 'PNG')
print(f"✅ Created {output_path}")
