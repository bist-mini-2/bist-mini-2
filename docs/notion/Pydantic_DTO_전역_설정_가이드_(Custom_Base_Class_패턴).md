# Pydantic DTO 전역 설정 가이드 (Custom Base Class 패턴)

FastAPI 프로젝트에서 다수의 Pydantic DTO 모델을 작성할 때, `from_attributes=True` 등의 설정을 개별 클래스마다 중복하여 정의하지 않고 **전역적으로 한 번에 적용하고 관리하는 설계 패턴**을 설명합니다.


---


## **1. 개요 및 한계**

Pydantic v2에서 ORM 매핑 옵션(`from_attributes=True`)을 전역 설정하려 할 때, `BaseModel` 클래스 자체의 기본 메타데이터 속성을 동적으로 임의 수정(Monkey Patching)하는 것은 다음과 같은 이유로 권장되지 않습니다.

1. **타입 검사기 무력화**: VS Code의 Pylance나 PyCharm의 정적 타입 분석기가 구조를 해석하지 못해 타입 경고(Linter Warning)가 발생할 수 있습니다.
1. **코드 추적성 저하**: 다른 개발자가 코드를 읽을 때 설정이 어디서 어떻게 흘러왔는지 추적하기가 매우 어려워집니다.
따라서 파이썬 생태계에서는 **사용자 정의 베이스 DTO 클래스(Custom Base DTO)**를 구현하여 상속 구조로 설정을 전파하는 것이 표준 베스트 프랙티스로 사용됩니다.


---


## **2. 구현 및 활용 방법**


### **① 공통 베이스 DTO 모델 생성**

프로젝트의 공통 패키지 영역(예: `api/database/config/` 또는 공통 유틸리티)에 아래와 같이 `BaseDTO` 클래스를 정의합니다.


```python
# 파일 위치 예시: api/database/config/dto_base.py
from pydantic import BaseModel, ConfigDict

class BaseDTO(BaseModel):
    """
    프로젝트의 모든 DTO(Request/Response) 모델이 상속받을 공통 베이스 클래스입니다.
    """
    model_config = ConfigDict(
        # 1. ORM/Entity 객체의 속성(.속성명)을 기반으로 DTO 자동 변환 허용 (model_validate 사용 가능)
        from_attributes=True,

        # 2. (선택사항) 정의되지 않은 입력 필드가 들어왔을 때 무시하고 통과시킬지 여부
        # extra="ignore"
    )
```


### **② 개별 DTO 모델에서 활용 ([model.py](file:///d:/Repo/kosa-fastapi/api/di/model.py))**

기존에 `BaseModel`을 상속받던 모든 DTO 객체들을 우리가 정의한 `BaseDTO`를 상속받도록 바꿉니다.


```python
from datetime import datetime
from pydantic import Field, EmailStr
# 공통 베이스 DTO 가져오기 (실제 배치된 경로에 따라 임포트)
from api.database.config.dto_base import BaseDTO

# 1. 회원 등록 요청 DTO
class MemberJoinRequest(BaseDTO):  # BaseDTO 상속
    mid: str = Field(..., min_length=4, max_length=20, description="아이디")
    mname: str = Field(..., min_length=2, max_length=10, description="이름")
    mpassword: str = Field(..., min_length=8, description="비밀번호")
    memail: EmailStr = Field(..., description="이메일 주소")

# 2. 회원 등록 응답 DTO
class MemberJoinResponse(BaseDTO):  # BaseDTO 상속
    mid: str = Field(..., description="아이디")
    mname: str = Field(..., description="이름")
    memail: EmailStr = Field(..., description="이메일 주소")
    mdate: datetime = Field(default_factory=datetime.now, description="가입일")

    # 개별 model_config = ConfigDict(from_attributes=True) 가 중복되므로 제거 가능!
```


---


## **3. 이 패턴의 기대 효과**

1. **중복 코드의 최소화 (DRY 원칙 준수)**
  * 매번 모든 DTO 하단에 적어주어야 했던 `model_config = ConfigDict(from_attributes=True)` 선언이 생략되므로 코드가 경량화되고 가독성이 높아집니다.
1. **설정의 중앙 집약화**
  * 프로젝트 요구사항이 바뀌어 DTO 전체의 기본 행동 방식(예: 빈 공백 트림처리, 스네이크 케이스 ➔ 카멜 케이스 필드 자동 매핑 등)을 변경해야 할 때, `BaseDTO` 한 곳만 고치면 즉시 전역 반영됩니다.
1. **IDE와의 호환성 유지**
  * 정식 파이썬 상속 흐름을 따르므로 VS Code(Pylance) 등의 자동 완성, 호버 툴팁 기능이 유실되지 않고 안전하게 지원됩니다.
