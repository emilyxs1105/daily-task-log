"""
Run this once to generate the app icon: python generate_icon.py
Requires Pillow: pip install Pillow
"""
from PIL import Image, ImageDraw
import os

os.makedirs("assets", exist_ok=True)

img = Image.new("RGBA", (64, 64), (24, 95, 165, 255))
d = ImageDraw.Draw(img)

d.rectangle([10, 12, 54, 52], fill=(255, 255, 255), outline=(200, 220, 240), width=1)
d.rectangle([16, 20, 48, 26], fill=(24, 95, 165))
d.rectangle([16, 30, 48, 34], fill=(200, 220, 240))
d.rectangle([16, 38, 36, 42], fill=(200, 220, 240))
d.rectangle([40, 36, 54, 54], fill=(39, 174, 96), outline=(30, 140, 70), width=1)
d.line([43, 45, 46, 49], fill="white", width=2)
d.line([46, 49, 52, 40], fill="white", width=2)

img_ico = img.resize((32, 32), Image.LANCZOS)
img_ico.save("assets/icon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
print("Icon saved to assets/icon.ico")
