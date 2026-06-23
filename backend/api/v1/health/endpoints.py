import time
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from api.common.config import settings
from api.database.config.dto_base import SuccessResponse

router = APIRouter(prefix="/system", tags=["시스템 헬스체크"])

# Simple uptime counter reference
START_TIME = time.time()


@router.get("/health", response_model=SuccessResponse, summary="시스템 헬스체크 수행 API")
async def health_check():
    """FastAPI 서버의 상태와 가동 시간(uptime) 및 기본 설정을 조회하여 헬스체크를 수행합니다.

    Returns:
        SuccessResponse: 시스템 상태, 가동 시간, 설정 정보를 포함하는 성공 응답 객체.
    """
    uptime = time.time() - START_TIME
    return SuccessResponse(
        data={
            "status": "healthy",
            "app_name": settings.APP_NAME,
            "environment": settings.ENV,
            "uptime_seconds": round(uptime, 2),
            "debug_mode": settings.DEBUG,
            "version": "1.0.0"
        }
    )


@router.get("/erd", response_class=HTMLResponse, summary="데이터베이스 ERD 시각화 명세서 API")
async def get_erd():
    """데이터베이스 라이브 스키마를 동적으로 역공학(Reflection)하여 Mermaid ERD 다이어그램 웹사이트를 생성 및 반환합니다.

    Returns:
        HTMLResponse: 스타일링이 완비된 대화형 실시간 데이터베이스 ERD 웹페이지.
    """
    from sqlalchemy import inspect
    from api.database.config.dbsession import engine

    # 모든 SQLAlchemy 모델 클래스를 로딩하여 메타데이터에 등록 보장
    from api.v1.member.entity import MemberEntity
    from api.v1.research_gap.entity import ResearchGapTaskEntity
    from api.v1.chat.entity import ChatSessionEntity, ChatSourceEntity
    from api.v1.gems.entity import GemEntity
    from api.v1.notification.entity import NotificationEntity
    from api.v1.defense_arena.entity import DefenseArenaSessionEntity, DefenseArenaChunkEntity, DefenseHistoryEntity

    def reflect_db(connection):
        """커넥션을 이용하여 데이터베이스 스키마 및 제약 조건을 동적으로 스캔(Reflection)합니다."""
        inspector = inspect(connection)
        tables_data = {}
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            pk_names = inspector.get_pk_constraint(table_name).get("constrained_columns", [])
            fkeys = inspector.get_foreign_keys(table_name)
            tables_data[table_name] = {
                "columns": columns,
                "pks": pk_names,
                "fkeys": fkeys
            }
        return tables_data

    async with engine.connect() as conn:
        db_schema = await conn.run_sync(reflect_db)

    lines = ["erDiagram"]
    relationships = []
    seen_relations = set()

    for table_name, data in db_schema.items():
        lines.append(f"    {table_name} {{")
        pks = data["pks"]
        fkeys = data["fkeys"]

        col_constraints = {}
        for col_name in pks:
            col_constraints[col_name] = "PK"
        for fk in fkeys:
            for col_name in fk["constrained_columns"]:
                col_constraints[col_name] = "FK"

        for col in data["columns"]:
            col_name = col["name"]
            type_str = str(col["type"]).split("(")[0].lower()
            if "varchar" in type_str:
                type_str = "varchar"
            elif "integer" in type_str or "int" in type_str:
                type_str = "int"
            elif "timestamp" in type_str or "datetime" in type_str:
                type_str = "datetime"
            elif "boolean" in type_str:
                type_str = "bool"
            elif "text" in type_str:
                type_str = "text"
            elif "json" in type_str:
                type_str = "json"
            elif "vector" in type_str:
                type_str = "vector"

            constraint = col_constraints.get(col_name, "")
            # 논리적 외래키 매핑용 플레이스홀더
            if col_name in ("member_id", "mid") and table_name != "member" and not constraint:
                constraint = "FK"

            lines.append(f"        {type_str} {col_name} {constraint}")

            # 관계선 생성 (물리적 외래키)
            for fk in fkeys:
                target_table = fk["referred_table"]
                for c_col in fk["constrained_columns"]:
                    if c_col == col_name:
                        rel_key = f"{target_table}->{table_name}"
                        if rel_key not in seen_relations:
                            seen_relations.add(rel_key)
                            relationships.append(f"    {target_table} ||--o{{ {table_name} : \"{col_name}\"")

            # 관계선 생성 (논리적 외래키 - member)
            if col_name in ("member_id", "mid") and table_name != "member":
                has_physical = any(fk["referred_table"] == "member" for fk in fkeys)
                if not has_physical:
                    rel_key = f"member->{table_name}"
                    if rel_key not in seen_relations:
                        seen_relations.add(rel_key)
                        relationships.append(f"    member ||--o{{ {table_name} : \"{col_name}\"")

        lines.append("    }")

    lines.extend(relationships)
    mermaid_code = "\n".join(lines)

    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{settings.APP_NAME} - Database ERD</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@300;400;500;600;700;800&family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {{
            --bg-color: #141614;
            --card-bg: rgba(28, 30, 28, 0.45);
            --card-border: rgba(163, 178, 156, 0.12);
            --text-primary: #e3e5e3;
            --text-secondary: #a3a8a3;
            --sage-green: #a3b29c;
            --sage-glow: rgba(163, 178, 156, 0.3);
            --accent-glow: rgba(163, 178, 156, 0.06);
            --font-outfit: 'Outfit', 'Inter', 'Noto Sans KR', sans-serif;
        }}

        body {{
            margin: 0;
            padding: 0;
            background-color: var(--bg-color);
            color: var(--text-primary);
            font-family: var(--font-outfit);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }}

        .blob {{
            position: absolute;
            border-radius: 50%;
            filter: blur(120px);
            z-index: 0;
            pointer-events: none;
            opacity: 0.15;
            background: var(--sage-green);
        }}
        .blob-1 {{
            width: 500px;
            height: 500px;
            top: -100px;
            left: -100px;
        }}
        .blob-2 {{
            width: 600px;
            height: 600px;
            bottom: -200px;
            right: -100px;
        }}

        header {{
            position: relative;
            z-index: 10;
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--card-border);
            background: rgba(20, 22, 20, 0.8);
            backdrop-filter: blur(10px);
        }}

        .logo {{
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 24px;
            font-weight: 800;
            color: var(--text-primary);
            text-decoration: none;
            letter-spacing: -0.5px;
        }}
        .logo i {{
            color: var(--sage-green);
            text-shadow: 0 0 15px var(--sage-glow);
        }}

        .back-btn {{
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            border-radius: 12px;
            border: 1px solid var(--card-border);
            background: var(--card-bg);
            color: var(--text-primary);
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            backdrop-filter: blur(20px);
        }}
        .back-btn:hover {{
            border-color: var(--sage-green);
            box-shadow: 0 0 15px var(--sage-glow);
            transform: translateY(-2px);
        }}

        main {{
            position: relative;
            z-index: 10;
            padding: 40px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 30px;
        }}

        .title-section {{
            text-align: center;
            margin-bottom: 10px;
        }}
        .title-section h1 {{
            font-size: 36px;
            font-weight: 800;
            margin: 0 0 10px 0;
            letter-spacing: -1px;
            background: linear-gradient(135deg, #ffffff 0%, var(--sage-green) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .title-section p {{
            color: var(--text-secondary);
            font-size: 16px;
            margin: 0;
        }}

        .erd-container {{
            width: 100%;
            max-width: 1200px;
            border-radius: 24px;
            border: 1px solid var(--card-border);
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            display: flex;
            justify-content: center;
            overflow: auto;
            position: relative;
        }}

        .mermaid {{
            width: 100%;
            background: transparent !important;
        }}

        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        ::-webkit-scrollbar-track {{
            background: rgba(20, 22, 20, 0.5);
        }}
        ::-webkit-scrollbar-thumb {{
            background: rgba(163, 178, 156, 0.3);
            border-radius: 5px;
        }}
        ::-webkit-scrollbar-thumb:hover {{
            background: var(--sage-green);
        }}
    </style>
</head>
<body>
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>

    <header>
        <a href="/" class="logo">
            <i class="bi bi-database-fill-gear"></i>
            <span>{settings.APP_NAME}</span>
        </a>
        <a href="/" class="back-btn">
            <i class="bi bi-arrow-left"></i>
            <span>메인으로 돌아가기</span>
        </a>
    </header>

    <main>
        <div class="title-section">
            <h1>Database ERD</h1>
            <p>SQLAlchemy ORM 메타데이터를 기반으로 실시간 자동 생성된 데이터베이스 개체 관계도입니다.</p>
        </div>

        <div class="erd-container">
            <pre class="mermaid">
{mermaid_code}
            </pre>
        </div>
    </main>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'dark',
            themeVariables: {{
                background: '#1c1e1c',
                primaryColor: '#2b2e2b',
                primaryTextColor: '#e3e5e3',
                lineColor: '#a3b29c',
                secondaryColor: '#1e211e',
                tertiaryColor: '#1c1e1c'
            }}
        }});
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

