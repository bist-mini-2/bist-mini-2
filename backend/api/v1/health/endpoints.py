import os
import time
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from api.common.config import settings
from api.database.config.dto_base import SuccessResponse

router = APIRouter(prefix="/system", tags=["시스템 헬스체크"])

# Simple uptime counter reference
START_TIME = time.time()

# Jinja2 템플릿 엔진 초기화
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "backend/templates"))


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



async def get_dashboard_context(request: Request) -> dict:
    """통합 개발자 대시보드(Bist DevPortal)에 필요한 모든 실시간 메타데이터를 수집하여 컨텍스트 딕셔너리로 반환합니다."""
    import os
    import subprocess
    import re
    from sqlalchemy import text, inspect
    from api.database.config.dbsession import engine

    # 모든 SQLAlchemy 모델 클래스를 로딩하여 메타데이터에 등록 보장
    from api.v1.member.entity import MemberEntity
    from api.v1.research_gap.entity import ResearchGapTaskEntity
    from api.v1.chat.entity import ChatSessionEntity, ChatSourceEntity
    from api.v1.gems.entity import GemEntity
    from api.v1.notification.entity import NotificationEntity
    from api.v1.defense_arena.entity import DefenseArenaSessionEntity, DefenseArenaChunkEntity, DefenseHistoryEntity

    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))

    # 1. Overview 데이터 수집
    uptime_seconds = round(time.time() - START_TIME, 2)
    uptime_str = f"{int(uptime_seconds // 3600)}시간 {int((uptime_seconds % 3600) // 60)}분 {int(uptime_seconds % 60)}초"

    # DB 연결 테스트
    db_connected = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_connected = True
    except Exception:
        pass

    openai_configured = bool(settings.OPENAI_API_KEY)

    # 2. API & Test Map 데이터 수집
    from fastapi.routing import APIRoute
    backend_routes = []
    for route in request.app.routes:
        if isinstance(route, APIRoute):
            # JWT 인증 필수 여부 확인
            auth_required = False
            for dep in route.dependant.dependencies:
                if dep.call and hasattr(dep.call, "__name__") and dep.call.__name__ in (
                    "verify_access_token", "check_roles", "get_current_user", "get_current_active_user"
                ):
                    auth_required = True
                    break

            # 매핑된 백엔드 테스트 파일 탐색
            test_file = None
            for tag in route.tags:
                tag_str = tag.value if hasattr(tag, "value") else str(tag)
                tag_lower = tag_str.lower()
                if "대화" in tag_str or "채팅" in tag_str or "chat" in tag_lower:
                    test_file = "tests/test_chat.py"
                elif "인증" in tag_str or "auth" in tag_lower:
                    test_file = "tests/test_auth.py"
                elif "회원" in tag_str or "member" in tag_lower:
                    test_file = "tests/test_member.py"
                elif "헬스체크" in tag_str or "health" in tag_lower:
                    test_file = "tests/test_health.py"
                elif "알림" in tag_str or "notification" in tag_lower:
                    test_file = "tests/test_notification.py"
                elif "디펜스" in tag_str or "defense" in tag_lower or "보안 아레나" in tag_str:
                    test_file = "tests/test_defense_arena.py"
                elif "논문 요약" in tag_str or "gem" in tag_lower:
                    test_file = "tests/test_gems.py"
                elif "연구 공백" in tag_str or "research" in tag_lower or "연구 스페이스" in tag_str:
                    test_file = "tests/test_research_gap.py"
                elif "유사도" in tag_str or "similarity" in tag_lower or "유사 논문" in tag_str:
                    test_file = "tests/test_similarity_search.py"

            test_exists = False
            if test_file:
                test_exists = os.path.exists(os.path.join(workspace_root, "backend", test_file))

            backend_routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "summary": route.summary or route.name,
                "description": (route.description or "").strip().split("\n")[0],
                "tags": list(route.tags),
                "auth_required": auth_required,
                "test_file": test_file or "N/A",
                "test_exists": test_exists
            })
    backend_routes.sort(key=lambda x: str(x["path"]))

    # 3. Next.js Router Map 데이터 수집
    frontend_src_app = os.path.join(workspace_root, "frontend/src/app")
    frontend_pages = []
    if os.path.exists(frontend_src_app):
        for root_dir, _, files in os.walk(frontend_src_app):
            for file in files:
                if file in ("page.js", "page.jsx"):
                    rel_dir = os.path.relpath(root_dir, frontend_src_app)
                    route_path = "/" if rel_dir == "." else f"/{rel_dir}"

                    # 프론트엔드 Jest 테스트 매핑
                    test_file = None
                    if "feature1" in route_path:
                        test_file = "tests/feature1.test.js"
                    elif "feature2" in route_path:
                        test_file = "tests/feature2.test.js"
                    elif "feature3" in route_path:
                        test_file = "tests/feature3.test.js"
                    elif "feature4" in route_path:
                        test_file = "tests/feature4.test.js"
                    elif "login" in route_path or "join" in route_path:
                        test_file = "tests/auth.test.js"

                    test_exists = False
                    if test_file:
                        test_exists = os.path.exists(os.path.join(workspace_root, "frontend", test_file))

                    frontend_pages.append({
                        "route": route_path,
                        "file_path": os.path.relpath(os.path.join(root_dir, file), workspace_root),
                        "test_file": test_file or "N/A",
                        "test_exists": test_exists
                    })
    frontend_pages.sort(key=lambda x: str(x["route"]))

    # 4. Settings & Config 데이터 수집 및 안전 마스킹
    config_fields = []
    for field in type(settings).model_fields.keys():
        val = getattr(settings, field)
        annotation = type(settings).model_fields[field].annotation
        if isinstance(annotation, type):
            type_str = annotation.__name__
        elif annotation is not None:
            type_str = str(annotation)
        else:
            type_str = "None"
        
        # 비밀번호, 토큰 키, 연결 주소 등 마스킹
        is_secret = any(k in field.lower() for k in ("secret", "key", "password", "url", "token"))
        display_val = str(val)
        if is_secret and val:
            if "postgresql" in display_val:
                display_val = re.sub(r":([^@/]+)@", r":***@", display_val)
            else:
                display_val = display_val[:4] + "********" + display_val[-4:] if len(display_val) > 8 else "********"
        elif not val:
            display_val = "(설정 없음)"

        config_fields.append({
            "key": field,
            "type": type_str,
            "value": display_val,
            "status": "Configured" if val else "Missing"
        })

    # 5. Git Changelog 수집 (최근 20개 커밋)
    git_changelog = []
    try:
        git_log = subprocess.check_output(
            ["git", "log", "-n", "20", "--pretty=format:%h|%an|%ar|%s"],
            cwd=workspace_root,
            text=True
        )
        for line in git_log.split("\n"):
            if "|" in line:
                h, an, ar, s = line.split("|", 3)
                git_changelog.append({
                    "hash": h,
                    "author": an,
                    "time": ar,
                    "subject": s
                })
    except Exception as e:
        git_changelog = [{"hash": "N/A", "author": "System", "time": "N/A", "subject": f"Git 로그 조회 실패: {str(e)}"}]

    # 6. Database ERD (Mermaid) 자동 재생성
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

    db_schema = {}
    if db_connected:
        try:
            async with engine.connect() as conn:
                db_schema = await conn.run_sync(reflect_db)
        except Exception as e:
            import logging
            logging.getLogger("uvicorn").error(f"Failed to reflect database schema: {e}")

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
            if col_name in ("member_id", "mid") and table_name != "member" and not constraint:
                constraint = "FK"

            lines.append(f"        {type_str} {col_name} {constraint}")

            for fk in fkeys:
                target_table = fk["referred_table"]
                for c_col in fk["constrained_columns"]:
                    if c_col == col_name:
                        rel_key = f"{target_table}->{table_name}"
                        if rel_key not in seen_relations:
                            seen_relations.add(rel_key)
                            relationships.append(f"    {target_table} ||--o{{ {table_name} : \"{col_name}\"")

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

    import json
    routes_json = json.dumps(backend_routes)
    pages_json = json.dumps(frontend_pages)
    config_json = json.dumps(config_fields)
    changelog_json = json.dumps(git_changelog)

    return {
        "app_name": settings.APP_NAME,
        "db_connected": db_connected,
        "openai_configured": openai_configured,
        "uptime_str": uptime_str,
        "env": settings.ENV,
        "debug_mode": settings.DEBUG,
        "backend_routes_count": len(backend_routes),
        "frontend_pages_count": len(frontend_pages),
        "routes_json": routes_json,
        "pages_json": pages_json,
        "config_json": config_json,
        "changelog_json": changelog_json,
        "mermaid_code": mermaid_code
    }


@router.get("/erd", response_class=HTMLResponse, include_in_schema=False)
async def get_erd(request: Request):
    """구식 ERD 엔드포인트 요청 시 신규 대시보드의 ERD 탭으로 리다이렉트합니다."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/#db-erd")


@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def get_dashboard(request: Request):
    """구식 대시보드 엔드포인트 요청 시 루트 포털('/')로 리다이렉트합니다."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/")


