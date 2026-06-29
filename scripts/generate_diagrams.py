import os
import math
from PIL import Image, ImageDraw, ImageFont

def get_font(size):
    # macOS system fonts supporting Korean
    font_paths = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",   # Primary macOS Korean font (Sandeol Gothic)
        "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf"
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()

# ---------------------------------------------------------
# DOCX Friendly Light & Transparent Theme Palette (RGBA)
# ---------------------------------------------------------
GROUP_BG = (248, 250, 252, 255)         # Light Slate background for containers
CARD_BG = (255, 255, 255, 255)          # White background for cards
SHADOW_COLOR = (226, 232, 240, 255)     # Very light grey shadow
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

def draw_rounded_rect(draw, coords, r, fill, outline=None, width=1):
    x1, y1, x2, y2 = coords
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill, outline=outline, width=width)

def draw_shadow_rect(draw, coords, r, fill, outline=None, width=1, shadow_offset=5):
    x1, y1, x2, y2 = coords
    # Draw soft light-grey shadow
    draw.rounded_rectangle([x1 + shadow_offset, y1 + shadow_offset, x2 + shadow_offset, y2 + shadow_offset], radius=r, fill=SHADOW_COLOR)
    # Draw main card
    draw.rounded_rectangle([x1, y1, x2, y2], radius=r, fill=fill, outline=outline, width=width)

def draw_arrow(draw, start, end, color, width=3):
    x1, y1 = start
    x2, y2 = end
    draw.line([x1, y1, x2, y2], fill=color, width=width)
    
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
    # Transparent canvas (RGBA), height reduced from 800 to 600
    img = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Fonts
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    # LEFT Box: Frontend Tier (Sky Blue accent) - y coordinates shifted up by 130
    draw_rounded_rect(draw, (80, 30, 520, 570), 12, fill=GROUP_BG, outline=ACCENT_SKY, width=2)
    draw.text((110, 50), "Frontend Tier (Next.js & Bootstrap 5)", fill=ACCENT_SKY, font=card_title_font)
    
    # Cards in Frontend
    cards_fe = [
        ("UI View Components", "React user interface components for Chat Hub,\nGap Analyzer and Gem Factory."),
        ("Global Context (Auth & State)", "React Context API to manage user session state\nand dynamic authentication state."),
        ("Axios HTTP Client", "Async REST API clients inside src/apis/ directory\nwith automated Bearer Token injection."),
        ("SSE Event Listener", "EventSource listener for backend real-time\nbackground tasks and token streaming.")
    ]
    
    y = 100
    for title, desc in cards_fe:
        draw_shadow_rect(draw, (110, y, 490, y + 100), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((130, y + 15), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((130, y + 45), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 115
        
    # RIGHT Box: Application Tier (Purple accent) - y coordinates shifted up
    draw_rounded_rect(draw, (680, 30, 1120, 570), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((710, 50), "Application Tier (FastAPI & Auth)", fill=ACCENT_PURPLE, font=card_title_font)
    
    # Cards in Application
    cards_app = [
        ("JWT Security & Auth Guard", "Decodes, parses and validates JWT signature.\nVerifies user credentials and session status."),
        ("APIRouter Gateway", "Dynamic API routing for Chat, Research Gap\nand Gem Factory business workflows.")
    ]
    
    y = 140
    for title, desc in cards_app:
        draw_shadow_rect(draw, (710, y, 1090, y + 120), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((730, y + 20), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((730, y + 55), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 180
        
    # Flows and Arrows
    # Axios client to Auth Guard
    draw_arrow(draw, (490, 390), (710, 200), color=FLOW_RED, width=3)
    draw.text((515, 250), "1. Bearer JWT Requests", fill=FLOW_RED, font=flow_font)
    
    # Auth Guard to API Router
    draw_arrow(draw, (900, 260), (900, 320), color=FLOW_GREEN, width=3)
    draw.text((920, 280), "2. Pass Authorized", fill=FLOW_GREEN, font=flow_font)
    
    # API Router back to SSE Reader
    draw_arrow(draw, (710, 400), (490, 505), color=FLOW_INDIGO, width=3)
    draw.text((505, 465), "3. Server-Sent Events", fill=FLOW_INDIGO, font=flow_font)
    
    img.save(output_path)

def generate_tier2(output_path):
    # Transparent canvas, height reduced to 600
    img = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    # Boundary box for Engine - shifted up
    draw_rounded_rect(draw, (120, 30, 1080, 570), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((150, 55), "LangGraph Multi-Agent Engine (Shared State: MultiAgentState)", fill=ACCENT_PURPLE, font=card_title_font)
    
    # Node 1: Analysis Node - shifted up by 130
    draw_shadow_rect(draw, (180, 250, 430, 370), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((200, 265), "AnalysisNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((200, 300), "Intent Analysis &\nDual Query Optimizer", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Node 2: Paper Node
    draw_shadow_rect(draw, (550, 110, 800, 230), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((570, 125), "PaperNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((570, 160), "pgvector RAG Search\nwith Cos Similarity Guard", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Node 3: Web Node
    draw_shadow_rect(draw, (550, 390, 800, 510), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((570, 405), "WebNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((570, 440), "Tavily Web Search API\nReal-time Market News", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Node 4: Synthesis Node
    draw_shadow_rect(draw, (920, 250, 1170, 370), 8, fill=CARD_BG, outline=ACCENT_SKY, width=1)
    draw.text((940, 265), "SynthesisNode", fill=ACCENT_SKY, font=card_title_font)
    draw.text((940, 300), "Cross-Reference\nJoins & Final Synthesis", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Arrows and flows
    # Start to Analysis
    draw_arrow(draw, (60, 310), (180, 310), color=FLOW_GREEN, width=3)
    draw.text((75, 280), "User Query", fill=FLOW_GREEN, font=flow_font)
    
    # Analysis to Paper (Parallel)
    draw_arrow(draw, (430, 280), (550, 170), color=FLOW_INDIGO, width=3)
    draw.text((435, 185), "Parallel Broadcast", fill=FLOW_INDIGO, font=flow_font)
    
    # Analysis to Web (Parallel)
    draw_arrow(draw, (430, 340), (550, 450), color=FLOW_INDIGO, width=3)
    draw.text((435, 420), "Parallel Broadcast", fill=FLOW_INDIGO, font=flow_font)
    
    # Paper to Synthesis (Merge)
    draw_arrow(draw, (800, 170), (920, 280), color=ACCENT_PURPLE, width=3)
    draw.text((820, 185), "Merge Context", fill=ACCENT_PURPLE, font=flow_font)
    
    # Web to Synthesis (Merge)
    draw_arrow(draw, (800, 450), (920, 340), color=ACCENT_PURPLE, width=3)
    draw.text((820, 420), "Merge Context", fill=ACCENT_PURPLE, font=flow_font)
    
    # Synthesis to out
    draw_arrow(draw, (1170, 310), (1240, 310), color=FLOW_RED, width=3)
    draw.text((1180, 280), "Yield", fill=FLOW_RED, font=flow_font)
    
    img.save(output_path)

def generate_tier3(output_path):
    # Transparent canvas, height reduced to 600
    img = Image.new("RGBA", (1200, 600), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    # LEFT Box: Application Services - shifted up
    draw_rounded_rect(draw, (80, 30, 480, 570), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((110, 50), "Application Services (FastAPI)", fill=ACCENT_PURPLE, font=card_title_font)
    
    app_services = [
        ("LangGraph Agent Engine", "Triggers Multi-Agent workflows & RAG search tools."),
        ("BackgroundTasks Workers", "Executes async batch research gap analysis task queue."),
        ("Business Service Layer", "Orchestrates API endpoints & coordinates DB access.")
    ]
    
    y = 110
    for title, desc in app_services:
        draw_shadow_rect(draw, (110, y, 450, y + 100), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((130, y + 15), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((130, y + 45), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 150
        
    # RIGHT Box: Database & Cache Tier (Green accent) - shifted up
    draw_rounded_rect(draw, (720, 30, 1120, 570), 12, fill=GROUP_BG, outline=ACCENT_EMERALD, width=2)
    draw.text((750, 50), "Database & Cache (Storage Tier)", fill=ACCENT_EMERALD, font=card_title_font)
    
    db_services = [
        ("PostgreSQL 17 DB", "Stores relational metadata: chat_session,\nchat_sources, and research_gap_task."),
        ("pgvector Vector Store", "HNSW 3072 index for bio/cs/astronomy.\nDynamic gem_{gem_id}_files isolation."),
        ("PostgresSaver (Checkpointer)", "Stores LangGraph chat history checkpoints\nand thread_id conversation states."),
        ("Redis In-Memory Cache", "Caches Citation Network relationships\nand repetitive RAG search queries.")
    ]
    
    y = 100
    for title, desc in db_services:
        draw_shadow_rect(draw, (750, y, 1090, y + 90), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((770, y + 12), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((770, y + 40), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 115
        
    # Flows and Connections
    # Agent to checkpointer
    draw_arrow(draw, (450, 160), (750, 350), color=FLOW_INDIGO, width=2)
    draw.text((470, 230), "Checkpoints (thread_id)", fill=FLOW_INDIGO, font=flow_font)
    
    # Agent to pgvector
    draw_arrow(draw, (450, 180), (750, 235), color=FLOW_RED, width=2)
    draw.text((490, 190), "Cosine Similarity Search", fill=FLOW_RED, font=flow_font)
    
    # BackgroundTasks to PostgreSQL
    draw_arrow(draw, (450, 310), (750, 145), color=ACCENT_PURPLE, width=2)
    draw.text((490, 310), "Task Progress & Translation", fill=ACCENT_PURPLE, font=flow_font)
    
    # Service to Redis
    draw_arrow(draw, (450, 460), (750, 465), color=ACCENT_EMERALD, width=2)
    draw.text((485, 440), "Citation Cache Hits", fill=ACCENT_EMERALD, font=flow_font)
    
    img.save(output_path)

def generate_physical_structure(output_path):
    # Transparent canvas (RGBA), height reduced to 420 for compact crop
    img = Image.new("RGBA", (1200, 420), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    card_title_font = get_font(18)
    card_body_font = get_font(13)
    flow_font = get_font(14)
    
    # Tier 1: Frontend (Left) - Title/Subtitle deleted, shifted up to y: 20
    draw_rounded_rect(draw, (50, 20, 380, 400), 12, fill=GROUP_BG, outline=ACCENT_SKY, width=2)
    draw.text((70, 40), "Frontend Tier (Next.js)", fill=ACCENT_SKY, font=card_title_font)
    
    # Content of Tier 1
    draw_shadow_rect(draw, (70, 90, 360, 370), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((90, 110), "• 반응형 대시보드 UI", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((90, 140), "Bootstrap 5 컴포넌트 기반 구조화\n모바일/데스크톱 최적화 레이아웃", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw.text((90, 210), "• SSE 실시간 렌더링", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((90, 240), "EventSource 수신부 구현\n비동기 완료 알림 및 토큰 스트리밍", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Tier 2: Application (Middle)
    draw_rounded_rect(draw, (460, 20, 790, 400), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((480, 40), "Application Tier (FastAPI)", fill=ACCENT_PURPLE, font=card_title_font)
    
    # Content of Tier 2
    draw_shadow_rect(draw, (480, 90, 770, 370), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((500, 110), "• 에이전트 오케스트레이션", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((500, 140), "LangGraph 다중 에이전트 엔진 구동\n사용자 정의 페르소나 (Gem) 빌드", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw.text((500, 210), "• 비동기 백그라운드 처리", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((500, 240), "FastAPI BackgroundTasks 연동\n대규모 문헌분석 오프로딩 구조", fill=TEXT_CARD_BODY, font=card_body_font)

    # Tier 3: Data Store (Right)
    draw_rounded_rect(draw, (870, 20, 1150, 400), 12, fill=GROUP_BG, outline=ACCENT_EMERALD, width=2)
    draw.text((890, 40), "Data Store Tier (Postgres)", fill=ACCENT_EMERALD, font=card_title_font)
    
    # Content of Tier 3
    draw_shadow_rect(draw, (890, 90, 1130, 370), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((910, 110), "• PostgreSQL 17", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((910, 140), "관계형 메타 및 대화기록 보존\nPostgresSaver checkpointer 탑재", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw.text((910, 210), "• pgvector 벡터 엔진", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((910, 240), "3072차원 HNSW 인덱싱\nGem별 동적 RAG 격리 컬렉션", fill=TEXT_CARD_BODY, font=card_body_font)

    # Connecting arrows
    draw_arrow(draw, (380, 160), (460, 160), color=FLOW_INDIGO, width=3)
    draw.text((395, 135), "API Request", fill=FLOW_TEXT, font=flow_font)
    
    draw_arrow(draw, (790, 160), (870, 160), color=FLOW_RED, width=3)
    draw.text((805, 135), "SQL / Query", fill=FLOW_TEXT, font=flow_font)
    
    # Back SSE flow
    draw_arrow(draw, (460, 280), (380, 280), color=FLOW_GREEN, width=3)
    draw.text((392, 290), "SSE Stream", fill=FLOW_TEXT, font=flow_font)
    
    img.save(output_path)

def generate_agent_workflow(output_path):
    # Transparent canvas, height reduced to 500 for compact crop
    img = Image.new("RGBA", (1200, 500), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    card_title_font = get_font(18)
    card_body_font = get_font(13)
    flow_font = get_font(14)
    point_font = get_font(15)
    
    # Title / Subtitle / Callout 박스 삭제하여 오직 노드 맵만 배치 (y shifted up by 120)
    # Process box 1: User Input
    draw_shadow_rect(draw, (60, 110, 220, 190), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((80, 130), "User Query", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((80, 160), "자연어 질의 수신", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Process box 2: AnalysisNode
    draw_shadow_rect(draw, (290, 90, 520, 210), 8, fill=CARD_BG, outline=ACCENT_PURPLE, width=1)
    draw.text((310, 110), "AnalysisNode", fill=ACCENT_PURPLE, font=card_title_font)
    draw.text((310, 140), "의도 분석 & 키워드 최적화\n(gpt-4o-mini 기용)", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Parallel Process box 3a: PaperNode
    draw_shadow_rect(draw, (620, 20, 840, 130), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((640, 40), "PaperNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((640, 70), "pgvector RAG 검색\n(Cos 유사도 0.35 필터)", fill=TEXT_CARD_BODY, font=card_body_font)

    # Parallel Process box 3b: WebNode
    draw_shadow_rect(draw, (620, 170, 840, 280), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((640, 190), "WebNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((640, 220), "Tavily Web Search API\n실시간 동향 수집", fill=TEXT_CARD_BODY, font=card_body_font)

    # Process box 4: SynthesisNode
    draw_shadow_rect(draw, (940, 90, 1160, 210), 8, fill=CARD_BG, outline=ACCENT_SKY, width=1)
    draw.text((960, 110), "SynthesisNode", fill=ACCENT_SKY, font=card_title_font)
    draw.text((960, 140), "크로스 레퍼런스 합성\n(gpt-4o 고성능 종합)", fill=TEXT_CARD_BODY, font=card_body_font)

    # Checkpointer Box (Bottom)
    draw_shadow_rect(draw, (440, 330, 760, 430), 8, fill=CARD_BG, outline=ACCENT_EMERALD, width=1)
    draw.text((460, 350), "PostgresSaver (Checkpointer)", fill=ACCENT_EMERALD, font=card_title_font)
    draw.text((460, 380), "스레드별 대화 히스토리 DB 자동 백업\n(상태전이 간 대화 맥락 영구 유지)", fill=TEXT_CARD_BODY, font=card_body_font)

    # Connecting Arrows
    draw_arrow(draw, (220, 150), (290, 150), color=FLOW_GREEN, width=2)
    
    # Broadcast to Parallel
    draw_arrow(draw, (520, 130), (620, 75), color=FLOW_INDIGO, width=2)
    draw_arrow(draw, (520, 170), (620, 225), color=FLOW_INDIGO, width=2)
    
    # Merge to Synthesis
    draw_arrow(draw, (840, 75), (940, 130), color=FLOW_INDIGO, width=2)
    draw.text((850, 85), "Merge", fill=FLOW_TEXT, font=flow_font)
    draw_arrow(draw, (840, 225), (940, 170), color=FLOW_INDIGO, width=2)
    draw.text((850, 200), "Merge", fill=FLOW_TEXT, font=flow_font)
    
    # Feedback / State Persistence
    draw_arrow(draw, (730, 150), (730, 330), color=FLOW_RED, width=2)
    draw_arrow(draw, (600, 330), (600, 150), color=FLOW_RED, width=2)
    draw.text((615, 240), "State Load/Save", fill=FLOW_RED, font=flow_font)

    img.save(output_path)

if __name__ == "__main__":
    os.makedirs("./docs/deliverables/4th", exist_ok=True)
    generate_tier1("./docs/deliverables/4th/system_architecture_tier1.png")
    generate_tier2("./docs/deliverables/4th/system_architecture_tier2.png")
    generate_tier3("./docs/deliverables/4th/system_architecture_tier3.png")
    generate_physical_structure("./docs/deliverables/4th/physical_system_structure.png")
    generate_agent_workflow("./docs/deliverables/4th/ai_agent_workflow.png")
    print("All transparent diagrams generated successfully with AppleSDGothicNeo font support!")
