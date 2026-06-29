import os
import math
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

# ---------------------------------------------------------
# DOCX Friendly Light Theme Palette
# ---------------------------------------------------------
BG_COLOR = "#FFFFFF"            # Pure White for document embedding
GROUP_BG = "#F8FAFC"            # Light Slate background for containers
CARD_BG = "#FFFFFF"             # White background for cards
SHADOW_COLOR = "#E2E8F0"        # Very light grey shadow
BORDER_COLOR = "#E2E8F0"        # Boundary border default

TEXT_TITLE = "#0F172A"          # Dark Slate (nearly black) for headings
TEXT_SUBTITLE = "#475569"       # Slate 600 for descriptions
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
    img = Image.new("RGB", (1200, 800), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    # Fonts
    title_font = get_font(36)
    subtitle_font = get_font(22)
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    # Title & Subtitle
    draw.text((50, 40), "Tier 1: Frontend & Auth (Client-to-Application)", fill=TEXT_TITLE, font=title_font)
    draw.text((50, 90), "Demonstrates client requests verification via Bearer JWT Auth Guard", fill=TEXT_SUBTITLE, font=subtitle_font)
    
    # LEFT Box: Frontend Tier (Sky Blue accent)
    draw_rounded_rect(draw, (80, 160, 520, 720), 12, fill=GROUP_BG, outline=ACCENT_SKY, width=2)
    draw.text((110, 180), "Frontend Tier (Next.js & Bootstrap 5)", fill=ACCENT_SKY, font=card_title_font)
    
    # Cards in Frontend
    cards_fe = [
        ("UI View Components", "React user interface components for Chat Hub,\nGap Analyzer and Gem Factory."),
        ("Global Context (Auth & State)", "React Context API to manage user session state\nand dynamic authentication state."),
        ("Axios HTTP Client", "Async REST API clients inside src/apis/ directory\nwith automated Bearer Token injection."),
        ("SSE Event Listener", "EventSource listener for backend real-time\nbackground tasks and token streaming.")
    ]
    
    y = 230
    for title, desc in cards_fe:
        draw_shadow_rect(draw, (110, y, 490, y + 100), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((130, y + 15), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((130, y + 45), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 120
        
    # RIGHT Box: Application Tier (Purple accent)
    draw_rounded_rect(draw, (680, 160, 1120, 720), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((710, 180), "Application Tier (FastAPI & Auth)", fill=ACCENT_PURPLE, font=card_title_font)
    
    # Cards in Application
    cards_app = [
        ("JWT Security & Auth Guard", "Decodes, parses and validates JWT signature.\nVerifies user credentials and session status."),
        ("APIRouter Gateway", "Dynamic API routing for Chat, Research Gap\nand Gem Factory business workflows.")
    ]
    
    y = 270
    for title, desc in cards_app:
        draw_shadow_rect(draw, (710, y, 1090, y + 120), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((730, y + 20), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((730, y + 55), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 180
        
    # Flows and Arrows
    # Axios client to Auth Guard
    draw_arrow(draw, (490, 520), (710, 330), color=FLOW_RED, width=3)
    draw.text((515, 380), "1. Bearer JWT Requests", fill=FLOW_RED, font=flow_font)
    
    # Auth Guard to API Router
    draw_arrow(draw, (900, 390), (900, 450), color=FLOW_GREEN, width=3)
    draw.text((920, 410), "2. Pass Authorized", fill=FLOW_GREEN, font=flow_font)
    
    # API Router back to SSE Reader
    draw_arrow(draw, (710, 530), (490, 640), color=FLOW_INDIGO, width=3)
    draw.text((505, 595), "3. Server-Sent Events", fill=FLOW_INDIGO, font=flow_font)
    
    img.save(output_path)

def generate_tier2(output_path):
    img = Image.new("RGB", (1200, 800), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    title_font = get_font(36)
    subtitle_font = get_font(22)
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    # Title & Subtitle
    draw.text((50, 40), "Tier 2: LangGraph Multi-Agent Engine", fill=TEXT_TITLE, font=title_font)
    draw.text((50, 90), "Deep-dive into Agent Orchestration, Parallel RAG & Synthesis Node", fill=TEXT_SUBTITLE, font=subtitle_font)
    
    # Boundary box for Engine
    draw_rounded_rect(draw, (120, 160, 1080, 720), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((150, 185), "LangGraph Multi-Agent Engine (Shared State: MultiAgentState)", fill=ACCENT_PURPLE, font=card_title_font)
    
    # Node 1: Analysis Node
    draw_shadow_rect(draw, (180, 380, 430, 500), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((200, 395), "AnalysisNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((200, 430), "Intent Analysis &\nDual Query Optimizer", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Node 2: Paper Node
    draw_shadow_rect(draw, (550, 240, 800, 360), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((570, 255), "PaperNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((570, 290), "pgvector RAG Search\nwith Cos Similarity Guard", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Node 3: Web Node
    draw_shadow_rect(draw, (550, 520, 800, 640), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((570, 535), "WebNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((570, 570), "Tavily Web Search API\nReal-time Market News", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Node 4: Synthesis Node
    draw_shadow_rect(draw, (920, 380, 1170, 500), 8, fill=CARD_BG, outline=ACCENT_SKY, width=1)
    draw.text((940, 395), "SynthesisNode", fill=ACCENT_SKY, font=card_title_font)
    draw.text((940, 430), "Cross-Reference\nJoins & Final Synthesis", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Arrows and flows
    # Start to Analysis
    draw_arrow(draw, (60, 440), (180, 440), color=FLOW_GREEN, width=3)
    draw.text((75, 410), "User Query", fill=FLOW_GREEN, font=flow_font)
    
    # Analysis to Paper (Parallel)
    draw_arrow(draw, (430, 410), (550, 300), color=FLOW_INDIGO, width=3)
    draw.text((435, 315), "Parallel Broadcast", fill=FLOW_INDIGO, font=flow_font)
    
    # Analysis to Web (Parallel)
    draw_arrow(draw, (430, 470), (550, 580), color=FLOW_INDIGO, width=3)
    draw.text((435, 550), "Parallel Broadcast", fill=FLOW_INDIGO, font=flow_font)
    
    # Paper to Synthesis (Merge)
    draw_arrow(draw, (800, 300), (920, 410), color=ACCENT_PURPLE, width=3)
    draw.text((820, 315), "Merge Context", fill=ACCENT_PURPLE, font=flow_font)
    
    # Web to Synthesis (Merge)
    draw_arrow(draw, (800, 580), (920, 470), color=ACCENT_PURPLE, width=3)
    draw.text((820, 550), "Merge Context", fill=ACCENT_PURPLE, font=flow_font)
    
    # Synthesis to out
    draw_arrow(draw, (1170, 440), (1240, 440), color=FLOW_RED, width=3)
    draw.text((1180, 410), "Yield", fill=FLOW_RED, font=flow_font)
    
    img.save(output_path)

def generate_tier3(output_path):
    img = Image.new("RGB", (1200, 800), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    title_font = get_font(36)
    subtitle_font = get_font(22)
    card_title_font = get_font(20)
    card_body_font = get_font(14)
    flow_font = get_font(16)
    
    # Title & Subtitle
    draw.text((50, 40), "Tier 3: Database & Cache Tier", fill=TEXT_TITLE, font=title_font)
    draw.text((50, 90), "Data Persistence, Vector Space Isolation & Caching Layer", fill=TEXT_SUBTITLE, font=subtitle_font)
    
    # LEFT Box: Application Services
    draw_rounded_rect(draw, (80, 160, 480, 720), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((110, 180), "Application Services (FastAPI)", fill=ACCENT_PURPLE, font=card_title_font)
    
    app_services = [
        ("LangGraph Agent Engine", "Triggers Multi-Agent workflows & RAG search tools."),
        ("BackgroundTasks Workers", "Executes async batch research gap analysis task queue."),
        ("Business Service Layer", "Orchestrates API endpoints & coordinates DB access.")
    ]
    
    y = 240
    for title, desc in app_services:
        draw_shadow_rect(draw, (110, y, 450, y + 100), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((130, y + 15), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((130, y + 45), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 150
        
    # RIGHT Box: Database & Cache Tier (Green accent)
    draw_rounded_rect(draw, (720, 160, 1120, 720), 12, fill=GROUP_BG, outline=ACCENT_EMERALD, width=2)
    draw.text((750, 180), "Database & Cache (Storage Tier)", fill=ACCENT_EMERALD, font=card_title_font)
    
    db_services = [
        ("PostgreSQL 17 DB", "Stores relational metadata: chat_session,\nchat_sources, and research_gap_task."),
        ("pgvector Vector Store", "HNSW 3072 index for bio/cs/astronomy.\nDynamic gem_{gem_id}_files isolation."),
        ("PostgresSaver (Checkpointer)", "Stores LangGraph chat history checkpoints\nand thread_id conversation states."),
        ("Redis In-Memory Cache", "Caches Citation Network relationships\nand repetitive RAG search queries.")
    ]
    
    y = 230
    for title, desc in db_services:
        draw_shadow_rect(draw, (750, y, 1090, y + 90), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
        draw.text((770, y + 12), title, fill=TEXT_CARD_TITLE, font=card_title_font)
        draw.text((770, y + 40), desc, fill=TEXT_CARD_BODY, font=card_body_font)
        y += 115
        
    # Flows and Connections
    # Agent to checkpointer
    draw_arrow(draw, (450, 290), (750, 480), color=FLOW_INDIGO, width=2)
    draw.text((470, 360), "Checkpoints (thread_id)", fill=FLOW_INDIGO, font=flow_font)
    
    # Agent to pgvector
    draw_arrow(draw, (450, 310), (750, 365), color=FLOW_RED, width=2)
    draw.text((490, 320), "Cosine Similarity Search", fill=FLOW_RED, font=flow_font)
    
    # BackgroundTasks to PostgreSQL
    draw_arrow(draw, (450, 440), (750, 275), color=ACCENT_PURPLE, width=2)
    draw.text((490, 440), "Task Progress & Translation", fill=ACCENT_PURPLE, font=flow_font)
    
    # Service to Redis
    draw_arrow(draw, (450, 590), (750, 595), color=ACCENT_EMERALD, width=2)
    draw.text((485, 570), "Citation Cache Hits", fill=ACCENT_EMERALD, font=flow_font)
    
    img.save(output_path)

def generate_physical_structure(output_path):
    img = Image.new("RGB", (1200, 600), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    title_font = get_font(30)
    subtitle_font = get_font(18)
    card_title_font = get_font(18)
    card_body_font = get_font(13)
    flow_font = get_font(14)
    
    # Title & Subtitle
    draw.text((50, 30), "3-1. 시스템 물리 구조 (3-Tier Physical Architecture)", fill=TEXT_TITLE, font=title_font)
    draw.text((50, 75), "보안 격리성 확보 및 유지보수 효율 극대화를 위한 물리 계층 분할 설계", fill=TEXT_SUBTITLE, font=subtitle_font)
    
    # Tier 1: Frontend (Left)
    draw_rounded_rect(draw, (50, 140, 380, 520), 12, fill=GROUP_BG, outline=ACCENT_SKY, width=2)
    draw.text((70, 160), "Frontend Tier (Next.js)", fill=ACCENT_SKY, font=card_title_font)
    
    # Content of Tier 1
    draw_shadow_rect(draw, (70, 210, 360, 490), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((90, 230), "• 반응형 대시보드 UI", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((90, 260), "Bootstrap 5 컴포넌트 기반 구조화\n모바일/데스크톱 최적화 레이아웃", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw.text((90, 330), "• SSE 실시간 렌더링", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((90, 360), "EventSource 수신부 구현\n비동기 완료 알림 및 토큰 스트리밍", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Tier 2: Application (Middle)
    draw_rounded_rect(draw, (460, 140, 790, 520), 12, fill=GROUP_BG, outline=ACCENT_PURPLE, width=2)
    draw.text((480, 160), "Application Tier (FastAPI)", fill=ACCENT_PURPLE, font=card_title_font)
    
    # Content of Tier 2
    draw_shadow_rect(draw, (480, 210, 770, 490), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((500, 230), "• 에이전트 오케스트레이션", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((500, 260), "LangGraph 다중 에이전트 엔진 구동\n사용자 정의 페르소나 (Gem) 빌드", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw.text((500, 330), "• 비동기 백그라운드 처리", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((500, 360), "FastAPI BackgroundTasks 연동\n대규모 문헌분석 오프로딩 구조", fill=TEXT_CARD_BODY, font=card_body_font)

    # Tier 3: Data Store (Right)
    draw_rounded_rect(draw, (870, 140, 1150, 520), 12, fill=GROUP_BG, outline=ACCENT_EMERALD, width=2)
    draw.text((890, 160), "Data Store Tier (Postgres)", fill=ACCENT_EMERALD, font=card_title_font)
    
    # Content of Tier 3
    draw_shadow_rect(draw, (890, 210, 1130, 490), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((910, 230), "• PostgreSQL 17", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((910, 260), "관계형 메타 및 대화기록 보존\nPostgresSaver checkpointer 탑재", fill=TEXT_CARD_BODY, font=card_body_font)
    
    draw.text((910, 330), "• pgvector 벡터 엔진", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((910, 360), "3072차원 HNSW 인덱싱\nGem별 동적 RAG 격리 컬렉션", fill=TEXT_CARD_BODY, font=card_body_font)

    # Connecting arrows
    draw_arrow(draw, (380, 280), (460, 280), color=FLOW_INDIGO, width=3)
    draw.text((395, 255), "API Request", fill=FLOW_TEXT, font=flow_font)
    
    draw_arrow(draw, (790, 280), (870, 280), color=FLOW_RED, width=3)
    draw.text((805, 255), "SQL / Query", fill=FLOW_TEXT, font=flow_font)
    
    # Back SSE flow
    draw_arrow(draw, (460, 400), (380, 400), color=FLOW_GREEN, width=3)
    draw.text((392, 410), "SSE Stream", fill=FLOW_TEXT, font=flow_font)
    
    # Title annotations at the bottom
    draw.text((120, 540), "[물리적 분리 차단: 기밀 데이터 유출 방지 및 보안성 보장]", fill=TEXT_SUBTITLE, font=flow_font)
    
    img.save(output_path)

def generate_agent_workflow(output_path):
    img = Image.new("RGB", (1200, 700), BG_COLOR)
    draw = ImageDraw.Draw(img)
    
    title_font = get_font(30)
    subtitle_font = get_font(18)
    card_title_font = get_font(18)
    card_body_font = get_font(13)
    flow_font = get_font(14)
    point_font = get_font(15)
    
    # Title & Subtitle
    draw.text((50, 30), "3-2. AI 에이전트 워크플로우 (Orchestration & Workflow)", fill=TEXT_TITLE, font=title_font)
    draw.text((50, 75), "LangGraph 기반의 듀얼 트랙 RAG, 영구 체크포인팅 및 듀얼 LLM 전략 구조", fill=TEXT_SUBTITLE, font=subtitle_font)
    
    # Process box 1: User Input
    draw_shadow_rect(draw, (60, 230, 220, 310), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((80, 250), "User Query", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((80, 280), "자연어 질의 수신", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Process box 2: AnalysisNode
    draw_shadow_rect(draw, (290, 210, 520, 330), 8, fill=CARD_BG, outline=ACCENT_PURPLE, width=1)
    draw.text((310, 230), "AnalysisNode", fill=ACCENT_PURPLE, font=card_title_font)
    draw.text((310, 260), "의도 분석 & 키워드 최적화\n(gpt-4o-mini 기용)", fill=TEXT_CARD_BODY, font=card_body_font)
    
    # Parallel Process box 3a: PaperNode
    draw_shadow_rect(draw, (620, 140, 840, 250), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((640, 160), "PaperNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((640, 190), "pgvector RAG 검색\n(Cos 유사도 0.35 필터)", fill=TEXT_CARD_BODY, font=card_body_font)

    # Parallel Process box 3b: WebNode
    draw_shadow_rect(draw, (620, 290, 840, 400), 8, fill=CARD_BG, outline=BORDER_COLOR, width=1)
    draw.text((640, 310), "WebNode", fill=TEXT_CARD_TITLE, font=card_title_font)
    draw.text((640, 340), "Tavily Web Search API\n실시간 동향 수집", fill=TEXT_CARD_BODY, font=card_body_font)

    # Process box 4: SynthesisNode
    draw_shadow_rect(draw, (940, 210, 1160, 330), 8, fill=CARD_BG, outline=ACCENT_SKY, width=1)
    draw.text((960, 230), "SynthesisNode", fill=ACCENT_SKY, font=card_title_font)
    draw.text((960, 260), "크로스 레퍼런스 합성\n(gpt-4o 고성능 종합)", fill=TEXT_CARD_BODY, font=card_body_font)

    # Checkpointer Box (Bottom)
    draw_shadow_rect(draw, (440, 450, 760, 550), 8, fill=CARD_BG, outline=ACCENT_EMERALD, width=1)
    draw.text((460, 470), "PostgresSaver (Checkpointer)", fill=ACCENT_EMERALD, font=card_title_font)
    draw.text((460, 500), "스레드별 대화 히스토리 DB 자동 백업\n(상태전이 간 대화 맥락 영구 유지)", fill=TEXT_CARD_BODY, font=card_body_font)

    # Connecting Arrows
    draw_arrow(draw, (220, 270), (290, 270), color=FLOW_GREEN, width=2)
    
    # Broadcast to Parallel
    draw_arrow(draw, (520, 250), (620, 195), color=FLOW_INDIGO, width=2)
    draw_arrow(draw, (520, 290), (620, 345), color=FLOW_INDIGO, width=2)
    
    # Merge to Synthesis
    draw_arrow(draw, (840, 195), (940, 250), color=FLOW_INDIGO, width=2)
    draw.text((850, 205), "Merge", fill=FLOW_TEXT, font=flow_font)
    draw_arrow(draw, (840, 345), (940, 290), color=FLOW_INDIGO, width=2)
    draw.text((850, 320), "Merge", fill=FLOW_TEXT, font=flow_font)
    
    # Feedback / State Persistence
    draw_arrow(draw, (730, 270), (730, 450), color=FLOW_RED, width=2)
    draw_arrow(draw, (600, 450), (600, 270), color=FLOW_RED, width=2)
    draw.text((615, 375), "State Load/Save", fill=FLOW_RED, font=flow_font)

    # Annotations / Callouts
    draw_rounded_rect(draw, (50, 580, 1150, 680), 8, fill=GROUP_BG, outline=BORDER_COLOR, width=1)
    draw.text((70, 595), "[에이전트 오케스트레이션 3대 핵심 포인트]", fill=TEXT_TITLE, font=point_font)
    draw.text((70, 620), "① 병렬 처리 (Parallelism): asyncio.gather 기반 RAG와 Web Node 동시 조회로 첫 타자 레이턴시 2.12초(23%) 단축", fill=TEXT_SUBTITLE, font=card_body_font)
    draw.text((70, 640), "② 상태 전이 (Persistence): PostgresSaver Checkpointer를 통한 대화 기록 영구 보존 및 Context 손실 제로", fill=TEXT_SUBTITLE, font=card_body_font)
    draw.text((70, 660), "③ 최적화 (Optimization): 가벼운 의도파악(gpt-4o-mini)과 무거운 최종종합(gpt-4o)의 2-Track 듀얼 LLM 전략 적용", fill=TEXT_SUBTITLE, font=card_body_font)

    img.save(output_path)

if __name__ == "__main__":
    os.makedirs("./docs/deliverables/4th", exist_ok=True)
    generate_tier1("./docs/deliverables/4th/system_architecture_tier1.png")
    generate_tier2("./docs/deliverables/4th/system_architecture_tier2.png")
    generate_tier3("./docs/deliverables/4th/system_architecture_tier3.png")
    generate_physical_structure("./docs/deliverables/4th/physical_system_structure.png")
    generate_agent_workflow("./docs/deliverables/4th/ai_agent_workflow.png")
    print("All diagrams generated successfully for DOCX report embedding!")
