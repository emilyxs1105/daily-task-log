"""Vibrant, theme-aware custom-generated modern icons using Pillow.
Avoids external assets and keeps the application 100% self-contained and lightweight.
"""
from PIL import Image, ImageDraw, ImageTk

_cache = {}

def get_icon(name, theme="light", size=20, selected=False):
    """Fetch or generate a cached ImageTk.PhotoImage for the specified icon."""
    cache_key = (name, theme, size, selected)
    if cache_key in _cache:
        return _cache[cache_key]
    
    img = _generate_icon_image(name, theme, size, selected)
    photo = ImageTk.PhotoImage(img)
    _cache[cache_key] = photo
    return photo

def _generate_icon_image(name, theme, size, selected=False):
    # Base drawings are designed at 80x80 for high resolution, then Lanczos downsampled to size
    temp_img = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
    td = ImageDraw.Draw(temp_img)
    
    is_dark = False
    
    if selected:
        # If selected (on a solid blue/red button background), use a premium translucent white scheme
        accent = (255, 255, 255, 255)
        muted_color = (255, 255, 255, 180)
        border_color = (255, 255, 255, 180)
        card_bg = (255, 255, 255, 40) # Frost glass effect
    else:
        accent = (10, 132, 255, 255) if is_dark else (0, 122, 255, 255)
        muted_color = (142, 142, 147, 255)
        border_color = (80, 80, 83, 255) if is_dark else (200, 200, 200, 255)
        card_bg = (44, 44, 46, 255) if is_dark else (255, 255, 255, 255)
    
    if name == "log":
        # Notepad paper body
        td.rounded_rectangle([15, 10, 65, 70], radius=8, fill=card_bg, outline=border_color, width=2)
        # Notepad blue top header
        td.rounded_rectangle([15, 10, 65, 24], radius=4, fill=accent)
        td.rectangle([15, 18, 65, 24], fill=accent) # Flatten header bottom
        # Notepad lines
        td.rectangle([25, 34, 55, 37], fill=muted_color)
        td.rectangle([25, 46, 48, 49], fill=muted_color)
        td.rectangle([25, 58, 52, 61], fill=muted_color)
        # Stylized diagonal orange pencil on the right
        pencil_color = (255, 255, 255, 220) if selected else (255, 149, 0, 255)
        td.line([(55, 60), (70, 35)], fill=pencil_color, width=6)
        td.line([(53, 63), (55, 60)], fill=(0, 0, 0, 255), width=6) # Lead tip
        
    elif name == "history":
        # Clipboard board
        board_bg = (255, 255, 255, 80) if selected else ((58, 58, 60, 255) if is_dark else (220, 220, 225, 255))
        td.rounded_rectangle([15, 15, 65, 75], radius=6, fill=board_bg)
        # Clipboard sheet
        td.rectangle([22, 26, 58, 70], fill=card_bg)
        # Clip at the top
        clip_color = (255, 255, 255, 255) if selected else ((142, 142, 147, 255) if is_dark else (70, 70, 75, 255))
        td.rounded_rectangle([32, 8, 48, 20], radius=3, fill=clip_color)
        # Checklists (vibrant green checkmarks + gray horizontal text bars)
        tick_color = (255, 255, 255, 255) if selected else (52, 199, 89, 255)
        td.line([(26, 38), (30, 42), (36, 33)], fill=tick_color, width=3)
        td.line([(40, 37), (54, 37)], fill=muted_color, width=3)
        td.line([(26, 52), (30, 56), (36, 47)], fill=tick_color, width=3)
        td.line([(40, 51), (50, 51)], fill=muted_color, width=3)
        
    elif name == "summary":
        # Baseline axis
        td.line([(15, 70), (65, 70)], fill=muted_color, width=3)
        # 3 rounded vertical bars (purple, blue, orange)
        bar1_color = (255, 255, 255, 180) if selected else (175, 82, 222, 255)
        bar2_color = accent
        bar3_color = (255, 255, 255, 120) if selected else (255, 149, 0, 255)
        td.rounded_rectangle([20, 42, 30, 67], radius=3, fill=bar1_color)
        td.rounded_rectangle([35, 22, 45, 67], radius=3, fill=bar2_color)
        td.rounded_rectangle([50, 32, 60, 67], radius=3, fill=bar3_color)
        
    elif name == "settings":
        # Symmetrical steel-gray mechanical gear
        gear_color = (255, 255, 255, 255) if selected else ((142, 142, 147, 255) if is_dark else (120, 120, 125, 255))
        td.line([(40, 15), (40, 65)], fill=gear_color, width=14)
        td.line([(15, 40), (65, 40)], fill=gear_color, width=14)
        td.line([(22, 22), (58, 58)], fill=gear_color, width=14)
        td.line([(22, 58), (58, 22)], fill=gear_color, width=14)
        td.ellipse([22, 22, 58, 58], fill=gear_color)
        td.ellipse([32, 32, 48, 48], fill=(0, 0, 0, 0)) # Central hole cutout
        
    elif name == "list":
        # 3 blue bullet points + gray lines
        td.ellipse([18, 21, 28, 31], fill=accent)
        td.line([(34, 26), (65, 26)], fill=muted_color, width=4)
        td.ellipse([18, 39, 28, 49], fill=accent)
        td.line([(34, 44), (65, 44)], fill=muted_color, width=4)
        td.ellipse([18, 57, 28, 67], fill=accent)
        td.line([(34, 62), (65, 62)], fill=muted_color, width=4)
        
    elif name == "calendar":
        # Calendar block
        td.rounded_rectangle([15, 15, 65, 67], radius=8, fill=card_bg, outline=border_color, width=2)
        # Vibrant red top header
        hdr_color = (255, 255, 255, 200) if selected else (255, 59, 48, 255)
        td.rounded_rectangle([15, 15, 65, 30], radius=4, fill=hdr_color)
        td.rectangle([15, 22, 65, 30], fill=hdr_color)
        # Grid dots (one highlighted in orange)
        dots = [
            (25, 42), (37, 42), (49, 42),
            (25, 54), (37, 54), (49, 54)
        ]
        for idx, (x, y) in enumerate(dots):
            dot_color = (255, 255, 255, 255) if selected else ((255, 149, 0, 255) if idx == 4 else muted_color)
            td.ellipse([x-3, y-3, x+3, y+3], fill=dot_color)
            
    elif name == "search":
        # Blue search circle ring
        td.ellipse([20, 20, 52, 52], outline=accent, width=6)
        # Gray diagonal handle
        td.line([(48, 48), (66, 66)], fill=muted_color, width=8)

    elif name == "holiday":
        # Vibrant sun and beach wave
        sun_color = (255, 255, 255, 255) if selected else (255, 204, 0, 255)
        sand_color = (255, 255, 255, 140) if selected else (255, 214, 10, 255)
        td.ellipse([45, 12, 69, 36], fill=sun_color)
        td.ellipse([10, 48, 70, 85], fill=sand_color)
        td.ellipse([30, 52, 90, 90], fill=accent)
        
    elif name == "leave":
        # Green palm tree
        trunk_color = (255, 255, 255, 160) if selected else (139, 87, 42, 255)
        td.line([(40, 70), (40, 35)], fill=trunk_color, width=6) # Trunk
        # Anti-aliased palm leaves radiating
        td.line([(40, 35), (25, 25)], fill=accent, width=8)
        td.line([(40, 35), (55, 25)], fill=accent, width=8)
        td.line([(40, 35), (20, 40)], fill=accent, width=8)
        td.line([(40, 35), (60, 40)], fill=accent, width=8)
        
    elif name == "mc":
        # Red circular badge with medical cross
        bg_color = (255, 255, 255, 80) if selected else (255, 69, 58, 255)
        td.ellipse([15, 15, 65, 65], fill=bg_color)
        td.line([(40, 28), (40, 52)], fill=(255, 255, 255, 255), width=8)
        td.line([(28, 40), (52, 40)], fill=(255, 255, 255, 255), width=8)
        
    elif name == "clear":
        # Red circle with white X
        bg_color = (255, 255, 255, 80) if selected else (255, 59, 48, 255)
        td.ellipse([18, 18, 62, 62], fill=bg_color)
        td.line([(31, 31), (49, 49)], fill=(255, 255, 255, 255), width=5)
        td.line([(49, 31), (31, 49)], fill=(255, 255, 255, 255), width=5)
        
    elif name == "add":
        # Green plus circle button
        bg_color = (255, 255, 255, 80) if selected else (52, 199, 89, 255)
        td.ellipse([18, 18, 62, 62], fill=bg_color)
        td.line([(40, 28), (40, 52)], fill=(255, 255, 255, 255), width=6)
        td.line([(28, 40), (52, 40)], fill=(255, 255, 255, 255), width=6)
        
    elif name == "copy":
        # Two overlapping sheet layers
        td.rounded_rectangle([26, 16, 64, 54], radius=6, fill=(0, 0, 0, 0), outline=muted_color, width=3)
        td.rounded_rectangle([16, 26, 54, 64], radius=6, fill=card_bg, outline=accent, width=3)
        
    elif name == "todo":
        # Paper body
        td.rounded_rectangle([15, 8, 65, 72], radius=8, fill=card_bg, outline=border_color, width=2)
        tick_color = (255, 255, 255, 255) if selected else (52, 199, 89, 255)
        empty_outline = (255, 255, 255, 180) if selected else border_color
        # Row 1 — checked
        td.rounded_rectangle([22, 20, 34, 32], radius=3, fill=tick_color, outline=tick_color)
        td.line([(25, 26), (28, 29), (33, 22)], fill=(255, 255, 255, 255), width=2)
        td.line([(38, 26), (60, 26)], fill=muted_color, width=3)
        # Row 2 — checked
        td.rounded_rectangle([22, 39, 34, 51], radius=3, fill=tick_color, outline=tick_color)
        td.line([(25, 45), (28, 48), (33, 41)], fill=(255, 255, 255, 255), width=2)
        td.line([(38, 45), (57, 45)], fill=muted_color, width=3)
        # Row 3 — unchecked (pending)
        td.rounded_rectangle([22, 58, 34, 70], radius=3, fill=card_bg, outline=empty_outline, width=2)
        td.line([(38, 64), (62, 64)], fill=muted_color, width=3)

    elif name == "export":
        # Box container with diagonal share/export arrow
        td.line([(20, 60), (20, 35)], fill=muted_color, width=4)
        td.line([(20, 60), (55, 60)], fill=muted_color, width=4)
        td.line([(55, 60), (55, 45)], fill=muted_color, width=4)
        td.line([(32, 48), (58, 22)], fill=accent, width=5) # Arrow shaft
        td.line([(58, 22), (46, 22)], fill=accent, width=5) # Arrow head left
        td.line([(58, 22), (58, 34)], fill=accent, width=5) # Arrow head down

    # Downsample using anti-aliased Lanczos filter
    return temp_img.resize((size, size), Image.LANCZOS)
