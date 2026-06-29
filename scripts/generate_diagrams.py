import os
import math
from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------
# High-DPI (Retina/Print-quality) Scale Factor
# ---------------------------------------------------------
SCALE = 3  # Render PNGs at 3x resolution (e.g., 3600px width)

def get_font(size):
    scaled_size = int(size * SCALE)
    font_paths = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",   # Primary macOS Korean font (Sandeol Gothic)
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, scaled_size)
            except:
                pass
    return ImageFont.load_default()

# ---------------------------------------------------------
# DOCX Friendly Light Theme Palette
# ---------------------------------------------------------
GROUP_BG = (248, 250, 252, 255)         # Light Slate background for containers
GROUP_BG_HEX = "#F8FAFC"
CARD_BG = (255, 255, 255, 255)          # White background for cards
CARD_BG_HEX = "#FFFFFF"
SHADOW_COLOR = (226, 232, 240, 255)     # Very light grey shadow
SHADOW_COLOR_HEX = "#E2E8F0"
BORDER_COLOR = "#E2E8F0"                # Boundary border default

TEXT_CARD_TITLE = "#1E293B"     # Slate 800 for card names
TEXT_CARD_BODY = "#516075"      # Slate 500/600 for card details

# Group Accent Borders (Darker for light-background contrast)
ACCENT_SKY = "#0284C7"          # Sky 600 (Frontend)
ACCENT_PURPLE = "#7C3AED"       # Purple 600 (Application/Engine)
ACCENT_EMERALD = "#059669"      # Emerald 600 (Storage/DB)

# Flow Arrows (Vibrant, high-contrast)
FLOW_RED = "#E11D48"            # Rose 600
FLOW_GREEN = "#16A34A"          # Green 600
FLOW_INDIGO = "#4F46E5"         # Indigo 600
FLOW_TEXT = "#1E293B"

# ---------------------------------------------------------
# PNG Helpers
# ---------------------------------------------------------
def draw_rounded_rect(draw, coords, r, fill, outline=None, width=1):
    x1, y1, x2, y2 = [int(coord * SCALE) for coord in coords]
    scaled_r = int(r * SCALE)
    scaled_width = int(width * SCALE)
    draw.rounded_rectangle([x1, y1, x2, y2], radius=scaled_r, fill=fill, outline=outline, width=scaled_width)

def draw_shadow_rect(draw, coords, r, fill, outline=None, width=1, shadow_offset=5):
    x1, y1, x2, y2 = [int(coord * SCALE) for coord in coords]
    scaled_r = int(r * SCALE)
    scaled_width = int(width * SCALE)
    scaled_offset = int(shadow_offset * SCALE)
    
    draw.rounded_rectangle([x1 + scaled_offset, y1 + scaled_offset, x2 + scaled_offset, y2 + scaled_offset], radius=scaled_r, fill=SHADOW_COLOR)
    draw.rounded_rectangle([x1, y1, x2, y2], radius=scaled_r, fill=fill, outline=outline, width=scaled_width)

def draw_arrow(draw, start, end, color, width=3):
    x1, y1 = [int(coord * SCALE) for coord in start]
    x2, y2 = [int(coord * SCALE) for coord in end]
    scaled_width = int(width * SCALE)
    draw.line([x1, y1, x2, y2], fill=color, width=scaled_width)
    
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 12 * SCALE
    left_x = x2 - arrow_len * math.cos(angle - math.pi / 6)
    left_y = y2 - arrow_len * math.sin(angle - math.pi / 6)
    right_x = x2 - arrow_len * math.cos(angle + math.pi / 6)
    right_y = y2 - arrow_len * math.sin(angle + math.pi / 6)
    
    draw.polygon([x2, y2, left_x, left_y, right_x, right_y], fill=color)

# ---------------------------------------------------------
# SVG Vector Drawing Helper Class
# ---------------------------------------------------------
class SVGBuilder:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.elements = []
        
    def add_rect(self, coords, rx=0, fill="none", stroke="none", stroke_width=1, shadow=False, shadow_offset=5):
        x1, y1, x2, y2 = coords
        w = x2 - x1
        h = y2 - y1
        if shadow:
            # Add soft vector shadow behind
            self.elements.append(f'  <rect x="{x1 + shadow_offset}" y="{y1 + shadow_offset}" width="{w}" height="{h}" rx="{rx}" fill="{SHADOW_COLOR_HEX}" />')
        self.elements.append(f'  <rect x="{x1}" y="{y1}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}" />')
        
    def add_text(self, coord, text, font_size=14, font_weight="normal", fill="#000000", anchor="start"):
        x, y = coord
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_y = y + i * (font_size * 1.4)
            safe_line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            weight_style = ' font-weight="bold"' if font_weight == "bold" else ''
            self.elements.append(f'  <text x="{x}" y="{line_y}" font-family="Apple SD Gothic Neo, Arial, sans-serif" font-size="{font_size}" fill="{fill}" text-anchor="{anchor}"{weight_style}>{safe_line}</text>')
            
    def add_arrow(self, start, end, color="#000000", width=2):
        x1, y1 = start
        x2, y2 = end
        self.elements.append(f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}" stroke-linecap="round" />')
        
        angle = math.atan2(y2 - y1, x2 - x1)
        arrow_len = 12
        left_x = x2 - arrow_len * math.cos(angle - math.pi / 6)
        left_y = y2 - arrow_len * math.sin(angle - math.pi / 6)
        right_x = x2 - arrow_len * math.cos(angle + math.pi / 6)
        right_y = y2 - arrow_len * math.sin(angle + math.pi / 6)
        
        self.elements.append(f'  <polygon points="{x2},{y2} {left_x},{left_y} {right_x},{right_y}" fill="{color}" />')
        
    def save(self, file_path):
        xml = [
            '<?xml version="1.0" encoding="UTF-8" standalone="no"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">',
            '  <!-- Transparent Background -->',
            '  <rect width="100%" height="100%" fill="none" />'
        ]
        xml.extend(self.elements)
        xml.append('</svg>')
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(xml))

# ---------------------------------------------------------
# Tier 1 Drawings
# ---------------------------------------------------------
def generate_tier1(output_png, output_svg):
    # --- 1. Generate PNG (3x High-DPI) ---
    img = Image.new("RGBA", (1200 * SCALE, 600 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    draw_rounded_rect(draw, (80, 30, 520, 570), 12, fill=GROUP_BG, outline=ACCENT_SKY, width=2)
    draw.text((110 * SCALE, 50 * SCALE), "Frontend Tier (Next.js & Bootstrap 5)", fill=ACCENT_SKY, font=card_title_font)
    
    cards_fe = [
        ("UI View Components", "React user interface components for Chat Hub,\nGap Analyzer and Gem Factory."),
        ("Global Context (Auth & State)", "React Context API to manage user session state\nand dynamic authentication state."),
        ("Axios HTTP Client", "Async REST API clients inside src/apis/ directory\nwith automated Bearer Token injection."),
        ("SSE Event Listener", "EventSource listener for backend real-time\nbackground tasks and token streaming.")
    ]
    
    y = 100
    for title, desc in cards_fe:
        draw_shadow_rect(draw, (110, y, 490, y + 100), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((130 * SCALE, (y + 15) * SCALE), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((130 * SCALE, (y + 45) * SCALE), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 115
        
    draw_rounded_rect(draw, (680, 30, 1120, 570), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((710 * SCALE, 50 * SCALE), "Application Tier (FastAPI & Auth)", fill=ACCENT_PURPLE, font=card_title_font)
    
    cards_app = [
        ("JWT Security & Auth Guard", "Decodes, parses and validates JWT signature.\nVerifies user credentials and session status."),
        ("APIRouter Gateway", "Dynamic API routing for Chat, Research Gap\nand Gem Factory business workflows.")
    ]
    
    y = 140
    for title, desc in cards_app:
        draw_shadow_rect(draw, (710, y, 1090, y + 120), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((730 * SCALE, (y + 20) * SCALE), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((730 * SCALE, (y + 55) * SCALE), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 180
        
    draw_arrow(draw, (490, 390), (710, 200), color=FLOW_RED, width=3)
    draw.text((515 * SCALE, 250 * SCALE), "1. Bearer JWT Requests", fill=FLOW_RED, font=flow_font)
    
    draw_arrow(draw, (900, 260), (900, 320), color=FLOW_GREEN, width=3)
    draw.text((920 * SCALE, 280 * SCALE), "2. Pass Authorized", fill=FLOW_GREEN, font=flow_font)
    
    draw_arrow(draw, (710, 400), (490, 505), color=FLOW_INDIGO, width=3)
    draw.text((505 * SCALE, 465 * SCALE), "3. Server-Sent Events", fill=FLOW_INDIGO, font=flow_font)
    
    img.save(output_png)

    # --- 2. Generate SVG (Scalable Vector) ---
    svg = SVGBuilder(1200, 600)
    svg.add_rect((80, 30, 520, 570), rx=12, fill=GROUP_BG_HEX, stroke=ACCENT_SKY, stroke_width=2)
    svg.add_text((110, 50), "Frontend Tier (Next.js & Bootstrap 5)", font_size=20, font_weight="bold", fill=ACCENT_SKY)
    
    y = 100
    for title, desc in cards_fe:
        svg.add_rect((110, y, 490, y + 100), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
        svg.add_text((130, y + 15), title, font_size=20, font_weight="bold", fill=TEXT_CARD_TITLE)
        svg.add_text((130, y + 45), desc, font_size=14, fill=TEXT_CARD_BODY)
        y += 115
        
    svg.add_rect((680, 30, 1120, 570), rx=12, fill=GROUP_BG_HEX, stroke=ACCENT_PURPLE, stroke_width=2)
    svg.add_text((710, 50), "Application Tier (FastAPI & Auth)", font_size=20, font_weight="bold", fill=ACCENT_PURPLE)
    
    y = 140
    for title, desc in cards_app:
        svg.add_rect((710, y, 1090, y + 120), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
        svg.add_text((730, y + 20), title, font_size=20, font_weight="bold", fill=TEXT_CARD_TITLE)
        svg.add_text((730, y + 55), desc, font_size=14, fill=TEXT_CARD_BODY)
        y += 180
        
    svg.add_arrow((490, 390), (710, 200), color=FLOW_RED, width=3)
    svg.add_text((515, 250), "1. Bearer JWT Requests", font_size=16, fill=FLOW_RED)
    
    svg.add_arrow((900, 260), (900, 320), color=FLOW_GREEN, width=3)
    svg.add_text((920, 280), "2. Pass Authorized", font_size=16, fill=FLOW_GREEN)
    
    svg.add_arrow((710, 400), (490, 505), color=FLOW_INDIGO, width=3)
    svg.add_text((505, 465), "3. Server-Sent Events", font_size=16, fill=FLOW_INDIGO)
    
    svg.save(output_svg)


# ---------------------------------------------------------
# Tier 2 Drawings
# ---------------------------------------------------------
def generate_tier2(output_png, output_svg):
    img = Image.new("RGBA", (1200 * SCALE, 600 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    draw_rounded_rect(draw, (120, 30, 1080, 570), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((150 * SCALE, 55 * SCALE), "LangGraph Multi-Agent Engine (Shared State: MultiAgentState)", fill=ACCENT_PURPLE, font=card_title_font)
    
    draw_shadow_rect(draw, (180, 250, 430, 370), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((200 * SCALE, 265 * SCALE), "AnalysisNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((200 * SCALE, 300 * SCALE), "Intent Analysis &\nDual Query Optimizer", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw_shadow_rect(draw, (550, 110, 800, 230), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((570 * SCALE, 125 * SCALE), "PaperNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((570 * SCALE, 160 * SCALE), "pgvector RAG Search\nwith Cos Similarity Guard", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw_shadow_rect(draw, (550, 390, 800, 510), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((570 * SCALE, 405 * SCALE), "WebNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((570 * SCALE, 440 * SCALE), "Tavily Web Search API\nReal-time Market News", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw_shadow_rect(draw, (920, 250, 1170, 370), 8, fill=CARD_BG, outline=ACCENT_SKY, width=1)
    draw.text((940 * SCALE, 265 * SCALE), "SynthesisNode", fill=ACCENT_SKY, font=card_title_font)
    draw.text((940 * SCALE, 300 * SCALE), "Cross-Reference\nJoins & Final Synthesis", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw_arrow(draw, (60, 310), (180, 310), color=FLOW_GREEN, width=3)
    draw.text((75 * SCALE, 280 * SCALE), "User Query", fill=FLOW_GREEN, font=flow_font)
    
    draw_arrow(draw, (430, 280), (550, 170), color=FLOW_INDIGO, width=3)
    draw.text((435 * SCALE, 185 * SCALE), "Parallel Broadcast", fill=FLOW_INDIGO, font=flow_font)
    
    draw_arrow(draw, (430, 340), (550, 450), color=FLOW_INDIGO, width=3)
    draw.text((435 * SCALE, 420 * SCALE), "Parallel Broadcast", fill=FLOW_INDIGO, font=flow_font)
    
    draw_arrow(draw, (800, 170), (920, 280), color=ACCENT_PURPLE, width=3)
    draw.text((820 * SCALE, 185 * SCALE), "Merge Context", fill=ACCENT_PURPLE, font=flow_font)
    
    draw_arrow(draw, (800, 450), (920, 340), color=ACCENT_PURPLE, width=3)
    draw.text((820 * SCALE, 420 * SCALE), "Merge Context", fill=ACCENT_PURPLE, font=flow_font)
    
    draw_arrow(draw, (1170, 310), (1240, 310), color=FLOW_RED, width=3)
    draw.text((1180 * SCALE, 280 * SCALE), "Yield", fill=FLOW_RED, font=flow_font)
    
    img.save(output_png)

    # --- SVG ---
    svg = SVGBuilder(1200, 600)
    svg.add_rect((120, 30, 1080, 570), rx=12, fill=GROUP_BG_HEX, stroke=ACCENT_PURPLE, stroke_width=2)
    svg.add_text((150, 55), "LangGraph Multi-Agent Engine (Shared State: MultiAgentState)", font_size=20, font_weight="bold", fill=ACCENT_PURPLE)
    
    svg.add_rect((180, 250, 430, 370), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
    svg.add_text((200, 265), "AnalysisNode", font_size=20, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((200, 300), "Intent Analysis &\nDual Query Optimizer", font_size=14, fill=TEXT_CARD_BODY)
    
    svg.add_rect((550, 110, 800, 230), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
    svg.add_text((570, 125), "PaperNode", font_size=20, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((570, 160), "pgvector RAG Search\nwith Cos Similarity Guard", font_size=14, fill=TEXT_CARD_BODY)
    
    svg.add_rect((550, 390, 800, 510), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
    svg.add_text((570, 405), "WebNode", font_size=20, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((570, 440), "Tavily Web Search API\nReal-time Market News", font_size=14, fill=TEXT_CARD_BODY)
    
    svg.add_rect((920, 250, 1170, 370), rx=8, fill=CARD_BG_HEX, stroke=ACCENT_SKY, stroke_width=1, shadow=True)
    svg.add_text((940, 265), "SynthesisNode", font_size=20, font_weight="bold", fill=ACCENT_SKY)
    svg.add_text((940, 300), "Cross-Reference\nJoins & Final Synthesis", font_size=14, fill=TEXT_CARD_BODY)
    
    svg.add_arrow((60, 310), (180, 310), color=FLOW_GREEN, width=3)
    svg.add_text((75, 280), "User Query", font_size=16, fill=FLOW_GREEN)
    
    svg.add_arrow((430, 280), (550, 170), color=FLOW_INDIGO, width=3)
    svg.add_text((435, 185), "Parallel Broadcast", font_size=16, fill=FLOW_INDIGO)
    
    svg.add_arrow((430, 340), (550, 450), color=FLOW_INDIGO, width=3)
    svg.add_text((435, 420), "Parallel Broadcast", font_size=16, fill=FLOW_INDIGO)
    
    svg.add_arrow((800, 170), (920, 280), color=ACCENT_PURPLE, width=3)
    svg.add_text((820, 185), "Merge Context", font_size=16, fill=ACCENT_PURPLE)
    
    svg.add_arrow((800, 450), (920, 340), color=ACCENT_PURPLE, width=3)
    svg.add_text((820, 420), "Merge Context", font_size=16, fill=ACCENT_PURPLE)
    
    svg.add_arrow((1170, 310), (1240, 310), color=FLOW_RED, width=3)
    svg.add_text((1180, 280), "Yield", font_size=16, fill=FLOW_RED)
    
    svg.save(output_svg)


# ---------------------------------------------------------
# Tier 3 Drawings
# ---------------------------------------------------------
def generate_tier3(output_png, output_svg):
    img = Image.new("RGBA", (1200 * SCALE, 600 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    draw_rounded_rect(draw, (80, 30, 480, 570), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((110 * SCALE, 50 * SCALE), "Application Services (FastAPI)", fill=ACCENT_PURPLE, font=card_title_font)
    
    app_services = [
        ("LangGraph Agent Engine", "Triggers Multi-Agent workflows & RAG search tools."),
        ("BackgroundTasks Workers", "Executes async batch research gap analysis task queue."),
        ("Business Service Layer", "Orchestrates API endpoints & coordinates DB access.")
    ]
    
    y = 110
    for title, desc in app_services:
        draw_shadow_rect(draw, (110, y, 450, y + 100), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((130 * SCALE, (y + 15) * SCALE), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((130 * SCALE, (y + 45) * SCALE), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 150
        
    draw_rounded_rect(draw, (720, 30, 1120, 570), 12, fill=GROUP_BG, outline=ACCENT_EMERALD, width=2)
    draw.text((750 * SCALE, 50 * SCALE), "Database & Cache (Storage Tier)", fill=ACCENT_EMERALD, font=card_title_font)
    
    db_services = [
        ("PostgreSQL 17 DB", "Stores relational metadata: chat_session,\nchat_sources, and research_gap_task."),
        ("pgvector Vector Store", "HNSW 3072 index for bio/cs/astronomy.\nDynamic gem_{gem_id}_files isolation."),
        ("PostgresSaver (Checkpointer)", "Stores LangGraph chat history checkpoints\nand thread_id conversation states."),
        ("Redis In-Memory Cache", "Caches Citation Network relationships\nand repetitive RAG search queries.")
    ]
    
    y = 100
    for title, desc in db_services:
        draw_shadow_rect(draw, (750, y, 1090, y + 90), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((770 * SCALE, (y + 12) * SCALE), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((770 * SCALE, (y + 40) * SCALE), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 115
        
    draw_arrow(draw, (450, 160), (750, 350), color=FLOW_INDIGO, width=2)
    draw.text((470 * SCALE, 230 * SCALE), "Checkpoints (thread_id)", fill=FLOW_INDIGO, font=flow_font)
    
    draw_arrow(draw, (450, 180), (750, 235), color=FLOW_RED, width=2)
    draw.text((490 * SCALE, 190 * SCALE), "Cosine Similarity Search", fill=FLOW_RED, font=flow_font)
    
    draw_arrow(draw, (450, 310), (750, 145), color=ACCENT_PURPLE, width=2)
    draw.text((490 * SCALE, 310 * SCALE), "Task Progress & Translation", fill=ACCENT_PURPLE, font=flow_font)
    
    draw_arrow(draw, (450, 460), (750, 465), color=ACCENT_EMERALD, width=2)
    draw.text((485 * SCALE, 440 * SCALE), "Citation Cache Hits", fill=ACCENT_EMERALD, font=flow_font)
    
    img.save(output_png)

    # --- SVG ---
    svg = SVGBuilder(1200, 600)
    svg.add_rect((80, 30, 480, 570), rx=12, fill=GROUP_BG_HEX, stroke=ACCENT_PURPLE, stroke_width=2)
    svg.add_text((110, 50), "Application Services (FastAPI)", font_size=20, font_weight="bold", fill=ACCENT_PURPLE)
    
    y = 110
    for title, desc in app_services:
        svg.add_rect((110, y, 450, y + 100), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
        svg.add_text((130, y + 15), title, font_size=20, font_weight="bold", fill=TEXT_CARD_TITLE)
        svg.add_text((130, y + 45), desc, font_size=14, fill=TEXT_CARD_BODY)
        y += 150
        
    svg.add_rect((720, 30, 1120, 570), rx=12, fill=GROUP_BG_HEX, stroke=ACCENT_EMERALD, stroke_width=2)
    svg.add_text((750, 50), "Database & Cache (Storage Tier)", font_size=20, font_weight="bold", fill=ACCENT_EMERALD)
    
    y = 100
    for title, desc in db_services:
        svg.add_rect((750, y, 1090, y + 90), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
        svg.add_text((770, y + 12), title, font_size=20, font_weight="bold", fill=TEXT_CARD_TITLE)
        svg.add_text((770, y + 40), desc, font_size=14, fill=TEXT_CARD_BODY)
        y += 115
        
    svg.add_arrow((450, 160), (750, 350), color=FLOW_INDIGO, width=2)
    svg.add_text((470, 230), "Checkpoints (thread_id)", font_size=16, fill=FLOW_INDIGO)
    
    svg.add_arrow((450, 180), (750, 235), color=FLOW_RED, width=2)
    svg.add_text((490, 190), "Cosine Similarity Search", font_size=16, fill=FLOW_RED)
    
    svg.add_arrow((450, 310), (750, 145), color=ACCENT_PURPLE, width=2)
    svg.add_text((490, 310), "Task Progress & Translation", font_size=16, fill=ACCENT_PURPLE)
    
    svg.add_arrow((450, 460), (750, 465), color=ACCENT_EMERALD, width=2)
    svg.add_text((485, 440), "Citation Cache Hits", font_size=16, fill=ACCENT_EMERALD)
    
    svg.save(output_svg)


# ---------------------------------------------------------
# Physical Structure Drawings
# ---------------------------------------------------------
def generate_physical_structure(output_png, output_svg):
    img = Image.new("RGBA", (1200 * SCALE, 420 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    card_title_font = get_font(18)
    card_body_font = get_font(13)
    flow_font = get_font(14)
    
    draw_rounded_rect(draw, (50, 20, 380, 400), 12, fill=GROUP_BG, outline=ACCENT_SKY, width=2)
    draw.text((70 * SCALE, 40 * SCALE), "Frontend Tier (Next.js)", fill=ACCENT_SKY, font=card_title_font)
    
    draw_shadow_rect(draw, (70, 90, 360, 370), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((90 * SCALE, 110 * SCALE), "• 반응형 대시보드 UI", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((90 * SCALE, 140 * SCALE), "Bootstrap 5 컴포넌트 기반 구조화\n모바일/데스크톱 최적화 레이아웃", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw.text((90 * SCALE, 210 * SCALE), "• SSE 실시간 렌더링", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((90 * SCALE, 240 * SCALE), "EventSource 수신부 구현\n비동기 완료 알림 및 토큰 스트리밍", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw_rounded_rect(draw, (460, 20, 790, 400), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((480 * SCALE, 40 * SCALE), "Application Tier (FastAPI)", fill=ACCENT_PURPLE, font=card_title_font)
    
    draw_shadow_rect(draw, (480, 90, 770, 370), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((500 * SCALE, 110 * SCALE), "• 에이전트 오케스트레이션", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((500 * SCALE, 140 * SCALE), "LangGraph 다중 에이전트 엔진 구동\n사용자 정의 페르소나 (Gem) 빌드", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw.text((500 * SCALE, 210 * SCALE), "• 비동기 백그라운드 처리", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((500 * SCALE, 240 * SCALE), "FastAPI BackgroundTasks 연동\n대규모 문헌분석 오프로딩 구조", fill=TEXT_CARD_BODY, font=card_body_font)

    draw_rounded_rect(draw, (870, 20, 1150, 400), 12, fill=GROUP_BG, outline=ACCENT_EMERALD, width=2)
    draw.text((890 * SCALE, 40 * SCALE), "Data Store Tier (Postgres)", fill=ACCENT_EMERALD, font=card_title_font)
    
    draw_shadow_rect(draw, (890, 90, 1130, 370), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((910 * SCALE, 110 * SCALE), "• PostgreSQL 17", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((910 * SCALE, 140 * SCALE), "관계형 메타 및 대화기록 보존\nPostgresSaver checkpointer 탑재", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw.text((910 * SCALE, 210 * SCALE), "• pgvector 벡터 엔진", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((910 * SCALE, 240 * SCALE), "3072차원 HNSW 인덱싱\nGem별 동적 RAG 격리 컬렉션", fill=TEXT_CARD_BODY, font=card_body_font)

    draw_arrow(draw, (380, 160), (460, 160), color=FLOW_INDIGO, width=3)
    draw.text((395 * SCALE, 135 * SCALE), "API Request", fill=FLOW_TEXT, font=flow_font)
    
    draw_arrow(draw, (790, 160), (870, 160), color=FLOW_RED, width=3)
    draw.text((805 * SCALE, 135 * SCALE), "SQL / Query", fill=FLOW_TEXT, font=flow_font)
    
    draw_arrow(draw, (460, 280), (380, 280), color=FLOW_GREEN, width=3)
    draw.text((392 * SCALE, 290 * SCALE), "SSE Stream", fill=FLOW_TEXT, font=flow_font)
    
    img.save(output_png)

    # --- SVG ---
    svg = SVGBuilder(1200, 420)
    svg.add_rect((50, 20, 380, 400), rx=12, fill=GROUP_BG_HEX, stroke=ACCENT_SKY, stroke_width=2)
    svg.add_text((70, 40), "Frontend Tier (Next.js)", font_size=18, font_weight="bold", fill=ACCENT_SKY)
    svg.add_rect((70, 90, 360, 370), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
    svg.add_text((90, 110), "• 반응형 대시보드 UI", font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((90, 140), "Bootstrap 5 컴포넌트 기반 구조화\n모바일/데스크톱 최적화 레이아웃", font_size=13, fill=TEXT_CARD_BODY)
    svg.add_text((90, 210), "• SSE 실시간 렌더링", font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((90, 240), "EventSource 수신부 구현\n비동기 완료 알림 및 토큰 스트리밍", font_size=13, fill=TEXT_CARD_BODY)
    
    svg.add_rect((460, 20, 790, 400), rx=12, fill=GROUP_BG_HEX, stroke=ACCENT_PURPLE, stroke_width=2)
    svg.add_text((480, 40), "Application Tier (FastAPI)", font_size=18, font_weight="bold", fill=ACCENT_PURPLE)
    svg.add_rect((480, 90, 770, 370), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
    svg.add_text((500, 110), "• 에이전트 오케스트레이션", font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((500, 140), "LangGraph 다중 에이전트 엔진 구동\n사용자 정의 페르소나 (Gem) 빌드", font_size=13, fill=TEXT_CARD_BODY)
    svg.add_text((500, 210), "• 비동기 백그라운드 처리", font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((500, 240), "FastAPI BackgroundTasks 연동\n대규모 문헌분석 오프로딩 구조", font_size=13, fill=TEXT_CARD_BODY)
    
    svg.add_rect((870, 20, 1150, 400), rx=12, fill=GROUP_BG_HEX, stroke=ACCENT_EMERALD, stroke_width=2)
    svg.add_text((890, 40), "Data Store Tier (Postgres)", font_size=18, font_weight="bold", fill=ACCENT_EMERALD)
    svg.add_rect((890, 90, 1130, 370), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
    svg.add_text((910, 110), "• PostgreSQL 17", font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((910, 140), "관계형 메타 및 대화기록 보존\nPostgresSaver checkpointer 탑재", font_size=13, fill=TEXT_CARD_BODY)
    svg.add_text((910, 210), "• pgvector 벡터 엔진", font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((910, 240), "3072차원 HNSW 인덱싱\nGem별 동적 RAG 격리 컬렉션", font_size=13, fill=TEXT_CARD_BODY)
    
    svg.add_arrow((380, 160), (460, 160), color=FLOW_INDIGO, width=3)
    svg.add_text((395, 135), "API Request", font_size=14, fill=FLOW_TEXT)
    
    svg.add_arrow((790, 160), (870, 160), color=FLOW_RED, width=3)
    svg.add_text((805, 135), "SQL / Query", font_size=14, fill=FLOW_TEXT)
    
    svg.add_arrow((460, 280), (380, 280), color=FLOW_GREEN, width=3)
    svg.add_text((392, 290), "SSE Stream", font_size=14, fill=FLOW_TEXT)
    
    svg.save(output_svg)


# ---------------------------------------------------------
# Agent Workflow Drawings
# ---------------------------------------------------------
def generate_agent_workflow(output_png, output_svg):
    img = Image.new("RGBA", (1200 * SCALE, 500 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    card_title_font = get_font(18)
    card_body_font = get_font(13)
    flow_font = get_font(14)
    
    draw_shadow_rect(draw, (60, 110, 220, 190), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((80 * SCALE, 130 * SCALE), "User Query", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((80 * SCALE, 160 * SCALE), "자연어 질의 수신", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw_shadow_rect(draw, (290, 90, 520, 210), 8, fill=CARD_BG, outline=ACCENT_PURPLE, width=1)
    draw.text((310 * SCALE, 110 * SCALE), "AnalysisNode", fill=ACCENT_PURPLE, font=card_title_font)
    draw.text((310 * SCALE, 140 * SCALE), "의도 분석 & 키워드 최적화\n(gpt-4o-mini 기용)", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw_shadow_rect(draw, (620, 20, 840, 130), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((640 * SCALE, 40 * SCALE), "PaperNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((640 * SCALE, 70 * SCALE), "pgvector RAG 검색\n(Cos 유사도 0.35 필터)", fill=TEXT_CARD_BODY, font=card_body_font)

    draw_shadow_rect(draw, (620, 170, 840, 280), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((640 * SCALE, 190 * SCALE), "WebNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((640 * SCALE, 220 * SCALE), "Tavily Web Search API\n실시간 동향 수집", fill=TEXT_CARD_BODY, font=card_body_font)

    draw_shadow_rect(draw, (940, 90, 1160, 210), 8, fill=CARD_BG, outline=ACCENT_SKY, width=1)
    draw.text((960 * SCALE, 110 * SCALE), "SynthesisNode", fill=ACCENT_SKY, font=card_title_font)
    draw.text((960 * SCALE, 140 * SCALE), "크로스 레퍼런스 합성\n(gpt-4o 고성능 종합)", fill=TEXT_CARD_BODY, font=card_body_font)

    draw_shadow_rect(draw, (440, 330, 760, 430), 8, fill=CARD_BG, outline=ACCENT_EMERALD, width=1)
    draw.text((460 * SCALE, 350 * SCALE), "PostgresSaver (Checkpointer)", fill=ACCENT_EMERALD, font=card_title_font)
    draw.text((460 * SCALE, 380 * SCALE), "스레드별 대화 히스토리 DB 자동 백업\n(상태전이 간 대화 맥락 영구 유지)", fill=TEXT_CARD_BODY, font=card_body_font)

    draw_arrow(draw, (220, 150), (290, 150), color=FLOW_GREEN, width=2)
    
    draw_arrow(draw, (520, 130), (620, 75), color=FLOW_INDIGO, width=2)
    draw_arrow(draw, (520, 170), (620, 225), color=FLOW_INDIGO, width=2)
    
    draw_arrow(draw, (840, 75), (940, 130), color=FLOW_INDIGO, width=2)
    draw.text((850 * SCALE, 85 * SCALE), "Merge", fill=FLOW_TEXT, font=flow_font)
    draw_arrow(draw, (840, 225), (940, 170), color=FLOW_INDIGO, width=2)
    draw.text((850 * SCALE, 200 * SCALE), "Merge", fill=FLOW_TEXT, font=flow_font)
    
    draw_arrow(draw, (730, 150), (730, 330), color=FLOW_RED, width=2)
    draw_arrow(draw, (600, 330), (600, 150), color=FLOW_RED, width=2)
    draw.text((615 * SCALE, 240 * SCALE), "State Load/Save", fill=FLOW_RED, font=flow_font)

    img.save(output_png)

    # --- SVG ---
    svg = SVGBuilder(1200, 500)
    svg.add_rect((60, 110, 220, 190), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
    svg.add_text((80, 130), "User Query", font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((80, 160), "자연어 질의 수신", font_size=13, fill=TEXT_CARD_BODY)
    
    svg.add_rect((290, 90, 520, 210), rx=8, fill=CARD_BG_HEX, stroke=ACCENT_PURPLE, stroke_width=1, shadow=True)
    svg.add_text((310, 110), "AnalysisNode", font_size=18, font_weight="bold", fill=ACCENT_PURPLE)
    svg.add_text((310, 140), "의도 분석 & 키워드 최적화\n(gpt-4o-mini 기용)", font_size=13, fill=TEXT_CARD_BODY)
    
    svg.add_rect((620, 20, 840, 130), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
    svg.add_text((640, 40), "PaperNode", font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((640, 70), "pgvector RAG 검색\n(Cos 유사도 0.35 필터)", font_size=13, fill=TEXT_CARD_BODY)
    
    svg.add_rect((620, 170, 840, 280), rx=8, fill=CARD_BG_HEX, stroke=BORDER_COLOR, stroke_width=1, shadow=True)
    svg.add_text((640, 190), "WebNode", font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
    svg.add_text((640, 220), "Tavily Web Search API\n실시간 동향 수집", font_size=13, fill=TEXT_CARD_BODY)
    
    svg.add_rect((940, 90, 1160, 210), rx=8, fill=CARD_BG_HEX, stroke=ACCENT_SKY, stroke_width=1, shadow=True)
    svg.add_text((960, 110), "SynthesisNode", font_size=18, font_weight="bold", fill=ACCENT_SKY)
    svg.add_text((960, 140), "크로스 레퍼런스 합성\n(gpt-4o 고성능 종합)", font_size=13, fill=TEXT_CARD_BODY)
    
    svg.add_rect((440, 330, 760, 430), rx=8, fill=CARD_BG_HEX, stroke=ACCENT_EMERALD, stroke_width=1, shadow=True)
    svg.add_text((460, 350), "PostgresSaver (Checkpointer)", font_size=18, font_weight="bold", fill=ACCENT_EMERALD)
    svg.add_text((460, 380), "스레드별 대화 히스토리 DB 자동 백업\n(상태전이 간 대화 맥락 영구 유지)", font_size=13, fill=TEXT_CARD_BODY)
    
    svg.add_arrow((220, 150), (290, 150), color=FLOW_GREEN, width=2)
    svg.add_arrow((520, 130), (620, 75), color=FLOW_INDIGO, width=2)
    svg.add_arrow((520, 170), (620, 225), color=FLOW_INDIGO, width=2)
    
    svg.add_arrow((840, 75), (940, 130), color=FLOW_INDIGO, width=2)
    svg.add_text((850, 85), "Merge", font_size=14, fill=FLOW_TEXT)
    svg.add_arrow((840, 225), (940, 170), color=FLOW_INDIGO, width=2)
    svg.add_text((850, 200), "Merge", font_size=14, fill=FLOW_TEXT)
    
    svg.add_arrow((730, 150), (730, 330), color=FLOW_RED, width=2)
    svg.add_arrow((600, 330), (600, 150), color=FLOW_RED, width=2)
    svg.add_text((615, 240), "State Load/Save", font_size=14, fill=FLOW_RED)
    
    svg.save(output_svg)


# ---------------------------------------------------------
# UC-01 Flow Drawings
# ---------------------------------------------------------
def generate_usecase_hubs_rag_flow(output_png, output_svg):
    img = Image.new("RGBA", (1200 * SCALE, 300 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    step_font = get_font(15)
    title_font = get_font(18)
    body_font = get_font(13)
    
    steps = [
        ("Step 01", "한글 질문 입력", "사용자가 의문이 제기된\n학술 분야 및 신기술 관련\n한글 질문을 창에 입력"),
        ("Step 02", "쿼리 최적화 분해", "AnalysisNode 가 가동되어\n학술 RAG용 영어 키워드와\n실시간 Web 검색어 동시 추출"),
        ("Step 03", "병렬 RAG 타격", "asyncio.gather 에 의해\npaper_node 와 web_node 가\n비동기 병렬 방식으로 동시 실행"),
        ("Step 04", "지식 크로스 융합", "SynthesisNode 가 논문 이론과\n실시간 웹 동향 지식을 결합해\n인라인 인용이 담긴 리포트 합성"),
        ("Step 05", "실시간 스트리밍", "완성된 리포트를 실시간 토큰\n스트리밍으로 화면 출력 및\n출처와 후속 질문 정보 DB 적재")
    ]
    
    card_width = 190
    card_height = 220
    spacing = 40
    start_x = 50
    y = 40
    
    for i, (step, title, desc) in enumerate(steps):
        x = start_x + i * (card_width + spacing)
        accent = ACCENT_SKY if i % 2 == 0 else ACCENT_PURPLE
        draw_shadow_rect(draw, (x, y, x + card_width, y + card_height), 8, fill=CARD_BG, outline=accent, width=2)
        
        draw.text(( (x + 15) * SCALE, (y + 15) * SCALE ), step, fill=accent, font=step_font)
        draw.text(( (x + 15) * SCALE, (y + 40) * SCALE ), title, fill=TEXT_CARD_TITLE, font=title_font)
        draw.text(( (x + 15) * SCALE, (y + 80) * SCALE ), desc, fill=TEXT_CARD_BODY, font=body_font)
        
        if i < len(steps) - 1:
            arrow_start = (x + card_width, y + card_height // 2)
            arrow_end = (x + card_width + spacing, y + card_height // 2)
            draw_arrow(draw, arrow_start, arrow_end, color=FLOW_GREEN, width=2)
            
    img.save(output_png)

    # --- SVG ---
    svg = SVGBuilder(1200, 300)
    for i, (step, title, desc) in enumerate(steps):
        x = start_x + i * (card_width + spacing)
        accent = ACCENT_SKY if i % 2 == 0 else ACCENT_PURPLE
        svg.add_rect((x, y, x + card_width, y + card_height), rx=8, fill=CARD_BG_HEX, stroke=accent, stroke_width=2, shadow=True)
        svg.add_text((x + 15, y + 15), step, font_size=15, font_weight="bold", fill=accent)
        svg.add_text((x + 15, y + 40), title, font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
        svg.add_text((x + 15, y + 80), desc, font_size=13, fill=TEXT_CARD_BODY)
        
        if i < len(steps) - 1:
            svg.add_arrow((x + card_width, y + card_height // 2), (x + card_width + spacing, y + card_height // 2), color=FLOW_GREEN, width=2)
    svg.save(output_svg)


# ---------------------------------------------------------
# UC-02 Flow Drawings
# ---------------------------------------------------------
def generate_usecase_gap_analysis_flow(output_png, output_svg):
    img = Image.new("RGBA", (1200 * SCALE, 300 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    step_font = get_font(14)
    title_font = get_font(17)
    body_font = get_font(12)
    
    steps = [
        ("Step 01", "분석 세션 요청", "도메인(cs/bio/astro)\n지정 및 연구 분석 키워드\n서버에 전달"),
        ("Step 02", "비동기 오프로딩", "즉시 task_id 발급 후\nFastAPI BackgroundTasks\n스레드로 연산 오프로딩"),
        ("Step 03", "4대 핵심문헌 선출", "pgvector 에서 유사 25편\n청크 조회 후 중복 필터링\n독립 4개 핵심 논문 선출"),
        ("Step 04", "원어 팩트 요약", "gpt-4o-mini 구조화 출력,\nLimitations 요약문과\n영문 source_quote 결합"),
        ("Step 05", "공백/방향 합성", "4대 논문 한계 종합 ➡️\n공통 제약 사항 정리 및\n3선 미래 연구 방향 추론"),
        ("Step 06", "SSE 알림 및 번역", "작업 완료 상태 저장 ➡️\nSSE 브라우저 푸시 알림 ➡️\n온디맨드 다국어 번역 캐싱")
    ]
    
    card_width = 160
    card_height = 220
    spacing = 30
    start_x = 50
    y = 40
    
    for i, (step, title, desc) in enumerate(steps):
        x = start_x + i * (card_width + spacing)
        accent = ACCENT_EMERALD if i % 2 == 0 else ACCENT_PURPLE
        draw_shadow_rect(draw, (x, y, x + card_width, y + card_height), 8, fill=CARD_BG, outline=accent, width=2)
        
        draw.text(( (x + 12) * SCALE, (y + 15) * SCALE ), step, fill=accent, font=step_font)
        draw.text(( (x + 12) * SCALE, (y + 40) * SCALE ), title, fill=TEXT_CARD_TITLE, font=title_font)
        draw.text(( (x + 12) * SCALE, (y + 80) * SCALE ), desc, fill=TEXT_CARD_BODY, font=body_font)
        
        if i < len(steps) - 1:
            arrow_start = (x + card_width, y + card_height // 2)
            arrow_end = (x + card_width + spacing, y + card_height // 2)
            draw_arrow(draw, arrow_start, arrow_end, color=FLOW_INDIGO, width=2)
            
    img.save(output_png)

    # --- SVG ---
    svg = SVGBuilder(1200, 300)
    for i, (step, title, desc) in enumerate(steps):
        x = start_x + i * (card_width + spacing)
        accent = ACCENT_EMERALD if i % 2 == 0 else ACCENT_PURPLE
        svg.add_rect((x, y, x + card_width, y + card_height), rx=8, fill=CARD_BG_HEX, stroke=accent, stroke_width=2, shadow=True)
        svg.add_text((x + 12, y + 15), step, font_size=14, font_weight="bold", fill=accent)
        svg.add_text((x + 12, y + 40), title, font_size=17, font_weight="bold", fill=TEXT_CARD_TITLE)
        svg.add_text((x + 12, y + 80), desc, font_size=12, fill=TEXT_CARD_BODY)
        
        if i < len(steps) - 1:
            svg.add_arrow((x + card_width, y + card_height // 2), (x + card_width + spacing, y + card_height // 2), color=FLOW_INDIGO, width=2)
    svg.save(output_svg)


# ---------------------------------------------------------
# UC-03 Flow Drawings
# ---------------------------------------------------------
def generate_usecase_arena_defense_flow(output_png, output_svg):
    img = Image.new("RGBA", (1200 * SCALE, 300 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    step_font = get_font(15)
    title_font = get_font(18)
    body_font = get_font(13)
    
    steps = [
        ("Step 01", "기밀 PDF 업로드", "사용자가 논문 초안 전송,\n메모리 임시 파싱 및\n전용 pgvector 테이블 개설"),
        ("Step 02", "3대 에이전트 토론", "방법론 검토/신규성 분석/\n학술 에디터 에이전트가\n토론을 거쳐 리뷰서 생성"),
        ("Step 03", "가설 검증 다수결", "RAG DB 및 참고문서 기준\nN회 독립 추론을 실행해\n가설 참/거짓 다수결 판정"),
        ("Step 04", "심사위원 디펜스", "리뷰서 기반 취약점 지적,\n사용자 방어 논리 작성 시\n0~100점 실시간 채점 대화"),
        ("Step 05", "보안 소거 파쇄", "대화 종료 또는 세션 내\n30분 무활동 감지 시\n임시 파일/벡터 완전 파쇄")
    ]
    
    card_width = 190
    card_height = 220
    spacing = 40
    start_x = 50
    y = 40
    
    for i, (step, title, desc) in enumerate(steps):
        x = start_x + i * (card_width + spacing)
        accent = ACCENT_EMERALD if i % 2 == 0 else ACCENT_SKY
        draw_shadow_rect(draw, (x, y, x + card_width, y + card_height), 8, fill=CARD_BG, outline=accent, width=2)
        
        draw.text(( (x + 15) * SCALE, (y + 15) * SCALE ), step, fill=accent, font=step_font)
        draw.text(( (x + 15) * SCALE, (y + 40) * SCALE ), title, fill=TEXT_CARD_TITLE, font=title_font)
        draw.text(( (x + 15) * SCALE, (y + 80) * SCALE ), desc, fill=TEXT_CARD_BODY, font=body_font)
        
        if i < len(steps) - 1:
            arrow_start = (x + card_width, y + card_height // 2)
            arrow_end = (x + card_width + spacing, y + card_height // 2)
            draw_arrow(draw, arrow_start, arrow_end, color=FLOW_RED, width=2)
            
    img.save(output_png)

    # --- SVG ---
    svg = SVGBuilder(1200, 300)
    for i, (step, title, desc) in enumerate(steps):
        x = start_x + i * (card_width + spacing)
        accent = ACCENT_EMERALD if i % 2 == 0 else ACCENT_SKY
        svg.add_rect((x, y, x + card_width, y + card_height), rx=8, fill=CARD_BG_HEX, stroke=accent, stroke_width=2, shadow=True)
        svg.add_text((x + 15, y + 15), step, font_size=15, font_weight="bold", fill=accent)
        svg.add_text((x + 15, y + 40), title, font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
        svg.add_text((x + 15, y + 80), desc, font_size=13, fill=TEXT_CARD_BODY)
        
        if i < len(steps) - 1:
            svg.add_arrow((x + card_width, y + card_height // 2), (x + card_width + spacing, y + card_height // 2), color=FLOW_RED, width=2)
    svg.save(output_svg)


# ---------------------------------------------------------
# UC-04 Flow Drawings
# ---------------------------------------------------------
def generate_usecase_gem_factory_flow(output_png, output_svg):
    img = Image.new("RGBA", (1200 * SCALE, 300 * SCALE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    step_font = get_font(15)
    title_font = get_font(18)
    body_font = get_font(13)
    
    steps = [
        ("Step 01", "Gem 개설 및 설정", "사용자가 에이전트 이름,\n학술 참고 도메인 범위,\n맞춤형 페르소나 지침 기입"),
        ("Step 02", "격리 데이터셋 적재", "참고용 개별 연구 파일 주입,\n파싱 후 gem_{gem_id}_files\n전용 pgvector 공간 격리 생성"),
        ("Step 03", "2-트랙 병렬 대화", "공인 학술 DB 툴과\n격리 파일 RAG 툴 동시 연동,\n중복 제거 컨텍스트 턴 누적"),
        ("Step 04", "비서 삭제 및 파쇄", "Gem 영구 삭제 트리거 시\nCascade 규칙 메타 정보 소거,\npgvector 컬렉션 드롭 파쇄")
    ]
    
    card_width = 220
    card_height = 220
    spacing = 60
    start_x = 70
    y = 40
    
    for i, (step, title, desc) in enumerate(steps):
        x = start_x + i * (card_width + spacing)
        accent = ACCENT_PURPLE if i % 2 == 0 else ACCENT_EMERALD
        draw_shadow_rect(draw, (x, y, x + card_width, y + card_height), 8, fill=CARD_BG, outline=accent, width=2)
        
        draw.text(( (x + 18) * SCALE, (y + 15) * SCALE ), step, fill=accent, font=step_font)
        draw.text(( (x + 18) * SCALE, (y + 40) * SCALE ), title, fill=TEXT_CARD_TITLE, font=title_font)
        draw.text(( (x + 18) * SCALE, (y + 80) * SCALE ), desc, fill=TEXT_CARD_BODY, font=body_font)
        
        if i < len(steps) - 1:
            arrow_start = (x + card_width, y + card_height // 2)
            arrow_end = (x + card_width + spacing, y + card_height // 2)
            draw_arrow(draw, arrow_start, arrow_end, color=FLOW_INDIGO, width=2)
            
    img.save(output_png)

    # --- SVG ---
    svg = SVGBuilder(1200, 300)
    for i, (step, title, desc) in enumerate(steps):
        x = start_x + i * (card_width + spacing)
        accent = ACCENT_PURPLE if i % 2 == 0 else ACCENT_EMERALD
        svg.add_rect((x, y, x + card_width, y + card_height), rx=8, fill=CARD_BG_HEX, stroke=accent, stroke_width=2, shadow=True)
        svg.add_text((x + 18, y + 15), step, font_size=15, font_weight="bold", fill=accent)
        svg.add_text((x + 18, y + 40), title, font_size=18, font_weight="bold", fill=TEXT_CARD_TITLE)
        svg.add_text((x + 18, y + 80), desc, font_size=13, fill=TEXT_CARD_BODY)
        
        if i < len(steps) - 1:
            svg.add_arrow((x + card_width, y + card_height // 2), (x + card_width + spacing, y + card_height // 2), color=FLOW_INDIGO, width=2)
    svg.save(output_svg)


if __name__ == "__main__":
    os.makedirs("./docs/deliverables/4th", exist_ok=True)
    
    # 3-Tier System Architecture
    generate_tier1("./docs/deliverables/4th/system_architecture_tier1.png", "./docs/deliverables/4th/system_architecture_tier1.svg")
    generate_tier2("./docs/deliverables/4th/system_architecture_tier2.png", "./docs/deliverables/4th/system_architecture_tier2.svg")
    generate_tier3("./docs/deliverables/4th/system_architecture_tier3.png", "./docs/deliverables/4th/system_architecture_tier3.svg")
    
    # Physical Structure & Agent Workflow
    generate_physical_structure("./docs/deliverables/4th/physical_system_structure.png", "./docs/deliverables/4th/physical_system_structure.svg")
    generate_agent_workflow("./docs/deliverables/4th/ai_agent_workflow.png", "./docs/deliverables/4th/ai_agent_workflow.svg")
    
    # Use Case Flows
    generate_usecase_hubs_rag_flow("./docs/deliverables/4th/usecase_hubs_rag_flow.png", "./docs/deliverables/4th/usecase_hubs_rag_flow.svg")
    generate_usecase_gap_analysis_flow("./docs/deliverables/4th/usecase_gap_analysis_flow.png", "./docs/deliverables/4th/usecase_gap_analysis_flow.svg")
    generate_usecase_arena_defense_flow("./docs/deliverables/4th/usecase_arena_defense_flow.png", "./docs/deliverables/4th/usecase_arena_defense_flow.svg")
    generate_usecase_gem_factory_flow("./docs/deliverables/4th/usecase_gem_factory_flow.png", "./docs/deliverables/4th/usecase_gem_factory_flow.svg")
    
    print(f"All transparent PNGs and SVG Vector files generated successfully!")
