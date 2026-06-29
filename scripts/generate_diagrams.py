import os
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    # macOS system fonts
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Verdana.ttf",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()

def draw_rounded_rect(draw, coords, r, fill, outline=None, width=1):
    x1, y1, x2, y2 = coords
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill, outline=outline, width=width)

def draw_shadow_rect(draw, coords, r, fill, outline=None, width=1, shadow_offset=4):
    x1, y1, x2, y2 = coords
    # Draw shadow
    draw.rounded_rectangle([x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset], radius=r, fill="#0b0f19")
    # Draw main card
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill, outline=outline, width=width)

def draw_arrow(draw, start, end, color, width=3):
    x1, y1 = start
    x2, y2 = end
    draw.line([x1, y1, x2, y2], fill=color, width=width)
    
    # Draw arrow head
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    arrow_len = 12
    # Left wing
    left_x = x2 - arrow_len * math.cos(angle - math.pi / 6)
    left_y = y2 - arrow_len * math.sin(angle - math.pi / 6)
    # Right wing
    right_x = x2 - arrow_len * math.cos(angle + math.pi / 6)
    right_y = y2 - arrow_len * math.sin(angle + math.pi / 6)
    
    draw.polygon([x2, y2, left_x, left_y, right_x, right_y], fill=color)

def generate_tier1(output_path):
    img = Image.new("RGB", (1200, 800), "#0F172A")
    draw = ImageDraw.Draw(img)
    
    # Fonts
    title_font = get_font(36)
    subtitle_font = get_font(22)
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    # Title
    draw.text((50, 40), "Tier 1: Frontend & Auth (Client-to-Application)", fill="#F8FAFC", font=title_font)
    draw.text((50, 90), "Demonstrates client requests verification via Bearer JWT Auth Guard", fill="#94A3B8", font=subtitle_font)
    
    # LEFT Box: Frontend Tier (Sky Blue theme)
    draw_rounded_rect(draw, (80, 160, 520, 720), 12, fill="#1E293B", outline="#38BDF8", width=2)
    draw.text((110, 180), "Frontend Tier (Next.js & Bootstrap 5)", fill="#38BDF8", font=card_title_font)
    
    # Cards in Frontend
    cards_fe = [
        ("UI View Components", "React user interface components for Chat Hub,\nGap Analyzer and Gem Factory."),
        ("Global Context (Auth & State)", "React Context API to manage user session state\nand dynamic authentication state."),
        ("Axios HTTP Client", "Async REST API clients inside src/apis/ directory\nwith automated Bearer Token injection."),
        ("SSE Event Listener", "EventSource listener for backend real-time\nbackground tasks and token streaming.")
    ]
    
    y = 230
    for title, desc in cards_fe:
        draw_shadow_rect(draw, (110, y, 490, y + 100), 8, fill="#1E1E24", outline="#334155", width=1)
        draw.text((130, y + 15), title, fill="#F8FAFC", font=card_title_font)
        draw.text((130, y + 45), desc, fill="#94A3B8", font=card_body_font)
        y += 120
        
    # RIGHT Box: Application Tier (Purple theme)
    draw_rounded_rect(draw, (680, 160, 1120, 720), 12, fill="#1E293B", outline="#A855F7", width=2)
    draw.text((710, 180), "Application Tier (FastAPI & Auth)", fill="#A855F7", font=card_title_font)
    
    # Cards in Application
    cards_app = [
        ("JWT Security & Auth Guard", "Decodes, parses and validates JWT signature.\nVerifies user credentials and session status."),
        ("APIRouter Gateway", "Dynamic API routing for Chat, Research Gap\nand Gem Factory business workflows.")
    ]
    
    y = 270
    for title, desc in cards_app:
        draw_shadow_rect(draw, (710, y, 1090, y + 120), 8, fill="#1E1E24", outline="#334155", width=1)
        draw.text((730, y + 20), title, fill="#F8FAFC", font=card_title_font)
        draw.text((730, y + 55), desc, fill="#94A3B8", font=card_body_font)
        y += 180
        
    # Flows and Arrows
    # Axios client to Auth Guard
    draw_arrow(draw, (490, 520), (710, 330), color="#F43F5E", width=3)
    draw.text((515, 380), "1. Bearer JWT Requests", fill="#F43F5E", font=flow_font)
    
    # Auth Guard to API Router
    draw_arrow(draw, (900, 390), (900, 450), color="#10B981", width=3)
    draw.text((920, 410), "2. Pass Authorized", fill="#10B981", font=flow_font)
    
    # API Router back to SSE Reader
    draw_arrow(draw, (710, 530), (490, 640), color="#6366F1", width=3)
    draw.text((505, 595), "3. Server-Sent Events", fill="#6366F1", font=flow_font)
    
    img.save(output_path)

def generate_tier2(output_path):
    img = Image.new("RGB", (1200, 800), "#0F172A")
    draw = ImageDraw.Draw(img)
    
    title_font = get_font(36)
    subtitle_font = get_font(22)
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    # Title
    draw.text((50, 40), "Tier 2: LangGraph Multi-Agent Engine", fill="#F8FAFC", font=title_font)
    draw.text((50, 90), "Deep-dive into Agent Orchestration, Parallel RAG & Synthesis Node", fill="#94A3B8", font=subtitle_font)
    
    # Boundary box for Engine
    draw_rounded_rect(draw, (120, 160, 1080, 720), 12, fill="#1E293B", outline="#A855F7", width=2)
    draw.text((150, 185), "LangGraph Multi-Agent Engine (Shared State: MultiAgentState)", fill="#A855F7", font=card_title_font)
    
    # Node 1: Analysis Node
    draw_shadow_rect(draw, (180, 380, 430, 500), 8, fill="#1E1E24", outline="#334155", width=1)
    draw.text((200, 395), "AnalysisNode", fill="#F8FAFC", font=card_title_font)
    draw.text((200, 430), "Intent Analysis &\nDual Query Optimizer", fill="#94A3B8", font=card_body_font)
    
    # Node 2: Paper Node
    draw_shadow_rect(draw, (550, 240, 800, 360), 8, fill="#1E1E24", outline="#334155", width=1)
    draw.text((570, 255), "PaperNode", fill="#F8FAFC", font=card_title_font)
    draw.text((570, 290), "pgvector RAG Search\nwith Cos Similarity Guard", fill="#94A3B8", font=card_body_font)
    
    # Node 3: Web Node
    draw_shadow_rect(draw, (550, 520, 800, 640), 8, fill="#1E1E24", outline="#334155", width=1)
    draw.text((570, 535), "WebNode", fill="#F8FAFC", font=card_title_font)
    draw.text((570, 570), "Tavily Web Search API\nReal-time Market News", fill="#94A3B8", font=card_body_font)
    
    # Node 4: Synthesis Node
    draw_shadow_rect(draw, (920, 380, 1170, 500), 8, fill="#1E1E24", outline="#38BDF8", width=1)
    draw.text((940, 395), "SynthesisNode", fill="#38BDF8", font=card_title_font)
    draw.text((940, 430), "Cross-Reference\nJoins & Final Synthesis", fill="#94A3B8", font=card_body_font)
    
    # Arrows and flows
    # Start to Analysis
    draw_arrow(draw, (60, 440), (180, 440), color="#10B981", width=3)
    draw.text((75, 410), "User Query", fill="#10B981", font=flow_font)
    
    # Analysis to Paper (Parallel)
    draw_arrow(draw, (430, 410), (550, 300), color="#38BDF8", width=3)
    draw.text((435, 315), "Parallel Broadcast", fill="#38BDF8", font=flow_font)
    
    # Analysis to Web (Parallel)
    draw_arrow(draw, (430, 470), (550, 580), color="#38BDF8", width=3)
    draw.text((435, 550), "Parallel Broadcast", fill="#38BDF8", font=flow_font)
    
    # Paper to Synthesis (Merge)
    draw_arrow(draw, (800, 300), (920, 410), color="#A855F7", width=3)
    draw.text((820, 315), "Merge Context", fill="#A855F7", font=flow_font)
    
    # Web to Synthesis (Merge)
    draw_arrow(draw, (800, 580), (920, 470), color="#A855F7", width=3)
    draw.text((820, 550), "Merge Context", fill="#A855F7", font=flow_font)
    
    # Synthesis to out
    draw_arrow(draw, (1170, 440), (1240, 440), color="#F43F5E", width=3)
    draw.text((1180, 410), "Yield", fill="#F43F5E", font=flow_font)
    
    img.save(output_path)

def generate_tier3(output_path):
    img = Image.new("RGB", (1200, 800), "#0F172A")
    draw = ImageDraw.Draw(img)
    
    title_font = get_font(36)
    subtitle_font = get_font(22)
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    # Title
    draw.text((50, 40), "Tier 3: Database & Cache Tier", fill="#F8FAFC", font=title_font)
    draw.text((50, 90), "Data Persistence, Vector Space Isolation & Caching Layer", fill="#94A3B8", font=subtitle_font)
    
    # LEFT Box: Application Services
    draw_rounded_rect(draw, (80, 160, 480, 720), 12, fill="#1E293B", outline="#A855F7", width=2)
    draw.text((110, 180), "Application Services (FastAPI)", fill="#A855F7", font=card_title_font)
    
    app_services = [
        ("LangGraph Agent Engine", "Triggers Multi-Agent workflows & RAG search tools."),
        ("BackgroundTasks Workers", "Executes async batch research gap analysis task queue."),
        ("Business Service Layer", "Orchestrates API endpoints & coordinates DB access.")
    ]
    
    y = 240
    for title, desc in app_services:
        draw_shadow_rect(draw, (110, y, 450, y + 100), 8, fill="#1E1E24", outline="#334155", width=1)
        draw.text((130, y + 15), title, fill="#F8FAFC", font=card_title_font)
        draw.text((130, y + 45), desc, fill="#94A3B8", font=card_body_font)
        y += 150
        
    # RIGHT Box: Database & Cache Tier (Green theme)
    draw_rounded_rect(draw, (720, 160, 1120, 720), 12, fill="#1E293B", outline="#10B981", width=2)
    draw.text((750, 180), "Database & Cache (Storage Tier)", fill="#10B981", font=card_title_font)
    
    db_services = [
        ("PostgreSQL 17 DB", "Stores relational metadata: chat_session,\nchat_sources, and research_gap_task."),
        ("pgvector Vector Store", "HNSW 3072 index for bio/cs/astronomy.\nDynamic gem_{gem_id}_files isolation."),
        ("PostgresSaver (Checkpointer)", "Stores LangGraph chat history checkpoints\nand thread_id conversation states."),
        ("Redis In-Memory Cache", "Caches Citation Network relationships\nand repetitive RAG search queries.")
    ]
    
    y = 230
    for title, desc in db_services:
        draw_shadow_rect(draw, (750, y, 1090, y + 90), 8, fill="#1E1E24", outline="#334155", width=1)
        draw.text((770, y + 12), title, fill="#F8FAFC", font=card_title_font)
        draw.text((770, y + 40), desc, fill="#94A3B8", font=card_body_font)
        y += 115
        
    # Flows and Connections
    # Agent to checkpointer
    draw_arrow(draw, (450, 290), (750, 480), color="#38BDF8", width=2)
    draw.text((470, 360), "Checkpoints (thread_id)", fill="#38BDF8", font=flow_font)
    
    # Agent to pgvector
    draw_arrow(draw, (450, 310), (750, 365), color="#F43F5E", width=2)
    draw.text((490, 320), "Cosine Similarity Search", fill="#F43F5E", font=flow_font)
    
    # BackgroundTasks to PostgreSQL
    draw_arrow(draw, (450, 440), (750, 275), color="#A855F7", width=2)
    draw.text((490, 440), "Task Progress & Translation", fill="#A855F7", font=flow_font)
    
    # Service to Redis
    draw_arrow(draw, (450, 590), (750, 595), color="#10B981", width=2)
    draw.text((485, 570), "Citation Cache Hits", fill="#10B981", font=flow_font)
    
    img.save(output_path)

if __name__ == "__main__":
    os.makedirs("./docs/deliverables/4th", exist_ok=True)
    generate_tier1("./docs/deliverables/4th/system_architecture_tier1.png")
    generate_tier2("./docs/deliverables/4th/system_architecture_tier2.png")
    generate_tier3("./docs/deliverables/4th/system_architecture_tier3.png")
    print("Diagrams successfully generated!")
