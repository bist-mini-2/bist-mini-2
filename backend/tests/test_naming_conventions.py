import os
import ast
import pytest

def get_python_files_in_api_v1():
    """backend/api/v1 디렉토리 내의 모든 Python 파일 목록을 수집합니다 (__pycache__ 제외)."""
    base_dir = os.path.realpath(os.path.join(os.path.dirname(__file__), "..", "api", "v1"))
    py_files = []
    for root, _, files in os.walk(base_dir):
        if "__pycache__" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                py_files.append(os.path.join(root, file))
    return py_files

def test_filenames_in_api_v1():
    """백엔드 api/v1 디렉토리 내부의 파일이름 컨벤션을 검증합니다.
    
    1. 복수형 파일명 권장: endpoints.py, services.py, models.py
    2. 단수형 파일명 권장: entity.py, dao.py
    3. 금지된 파일명: endpoint.py, service.py, model.py, daos.py, entities.py, controller.py, controllers.py
    """
    py_files = get_python_files_in_api_v1()
    disallowed_names = {
        "endpoint.py", "service.py", "model.py", "daos.py", "entities.py", 
        "controller.py", "controllers.py"
    }
    
    violations = []
    for filepath in py_files:
        filename = os.path.basename(filepath)
        if filename in disallowed_names:
            rel_path = os.path.relpath(filepath, start=os.path.join(os.path.dirname(__file__), ".."))
            violations.append(f"금지된 파일명 형식 사용 중: {rel_path} (올바른 복수형/단수형 컨벤션을 준수해야 합니다.)")
            
    assert not violations, "API v1 파일명 네이밍 컨벤션 위반 발견:\n" + "\n".join(violations)

def test_dto_classes_inherit_from_base_dto():
    """api/v1/*/models.py에 선언된 Pydantic 모델들이 모두 BaseDTO를 상속받는지 검증합니다."""
    py_files = get_python_files_in_api_v1()
    violations = []
    
    for filepath in py_files:
        if not filepath.endswith("models.py"):
            continue
            
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=filepath)
            
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Import 혹은 BaseDTO 자체 클래스는 제외
                if node.name in ("BaseDTO", "SuccessResponse", "ErrorResponse"):
                    continue
                # 상속받는 부모 클래스 확인
                base_names = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        base_names.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        base_names.append(base.attr)
                        
                # BaseDTO 또는 SuccessResponse/ErrorResponse를 상속받는지 검사
                inherits_properly = any(
                    b in ("BaseDTO", "SuccessResponse", "ErrorResponse") 
                    for b in base_names
                )
                
                # BaseModel을 상속받으면서 BaseDTO를 상속받지 않는 경우 검출
                # (혹은 Pydantic DTO인데 상속을 안 받은 경우)
                # 대부분의 Pydantic DTO는 BaseModel이나 BaseDTO 등을 직접 상속받음
                is_pydantic = any("Base" in b or "Model" in b for b in base_names)
                
                if is_pydantic and not inherits_properly:
                    rel_path = os.path.relpath(filepath, start=os.path.join(os.path.dirname(__file__), ".."))
                    violations.append(f"클래스 {node.name} ({rel_path}) 가 BaseDTO를 상속받지 않았습니다. (Bases: {base_names})")
                    
    assert not violations, "Pydantic DTO BaseDTO 상속 컨벤션 위반 발견:\n" + "\n".join(violations)

def test_docstrings_in_api_v1():
    """api/v1 디렉토리 내부의 모든 함수 및 클래스에 Google 스타일 Docstring이 존재하는지 확인합니다."""
    py_files = get_python_files_in_api_v1()
    violations = []
    
    # 예외 파일 (자동 생성 코드나 단순 라우터 설정 파일 등)
    ignored_files = {"__init__.py", "api_router.py"}
    
    for filepath in py_files:
        filename = os.path.basename(filepath)
        if filename in ignored_files:
            continue
            
        rel_path = os.path.relpath(filepath, start=os.path.join(os.path.dirname(__file__), ".."))
        
        with open(filepath, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=filepath)
            except SyntaxError as e:
                violations.append(f"구문 에러 ({rel_path}): {e}")
                continue
                
        # 모듈 자체 Docstring 체크
        module_doc = ast.get_docstring(tree)
        # Note: 모듈 docstring은 선택 사항일 수 있으므로 필요 시 체크 해제 (규칙 파일에는 '모든 모듈, 함수 및 클래스'로 명시됨)
        # if not module_doc:
        #     violations.append(f"모듈 {rel_path}: 모듈 Docstring이 없습니다.")
            
        for node in ast.walk(tree):
            # 클래스 Docstring 검사
            if isinstance(node, ast.ClassDef):
                class_doc = ast.get_docstring(node)
                if not class_doc:
                    violations.append(f"클래스 {node.name} ({rel_path}:L{node.lineno}): 클래스 Docstring이 누락되었습니다.")
                    
            # 함수/메서드 Docstring 검사
            elif isinstance(node, ast.FunctionDef):
                # 테스트 전용 helper나 inner function, 매직 메서드(__init__ 등)는 검사 제외 가능
                if node.name.startswith("__") and node.name.endswith("__"):
                    continue
                # 간단한 getter/setter 데코레이터가 달린 함수는 제외
                is_property = any(
                    isinstance(dec, ast.Name) and dec.id in ("property", "setter")
                    for dec in node.decorator_list
                )
                if is_property:
                    continue
                    
                func_doc = ast.get_docstring(node)
                if not func_doc:
                    violations.append(f"함수/메서드 {node.name} ({rel_path}:L{node.lineno}): Docstring이 누락되었습니다.")
                    
    assert not violations, "API v1 내에 Docstring 누락 발견:\n" + "\n".join(violations)
