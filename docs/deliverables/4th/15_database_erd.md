# [4차 산출물] 15. 데이터베이스 ERD 명세서 (Database Entity-Relationship Diagram)

본 문서는 `bist-mini-2` 플랫폼의 관계형 데이터베이스(PostgreSQL) 및 pgvector 테이블 구조에 존재하는 물리 스키마 필드들과 테이블 간 관계(Relationships)를 명시한 ERD 명세서입니다.

---

## 💾 데이터베이스 ERD (Entity-Relationship Diagram)

> 📢 **[구글 독스 이미지 삽입 안내 - ERD]**
> *   구글 독스 메뉴의 `삽입 ➡️ 이미지 ➡️ 컴퓨터에서 업로드`를 통해 아래 이미지 파일을 본문에 넣어주세요.
> *   **삽입 파일**: `docs/deliverables/4th/images/15_database_erd_architecture.png`

![15_database_erd_architecture](images/15_database_erd_architecture.png)

```mermaid
erDiagram
    member {
        string mid PK
        string mname
        string mpassword
        string memail
        boolean menabled
        string mrole
    }

    gem {
        string gem_id PK
        string member_id FK
        string name
        string db_sources
        string system_prompt
        boolean has_files
        datetime created_at
    }

    gem_file {
        string file_id PK
        string gem_id FK
        string filename
        integer chunk_count
        datetime uploaded_at
    }

    chat_session {
        string session_id PK
        string member_id FK
        string title
        datetime created_at
    }

    chat_source {
        integer id PK
        string session_id FK
        integer message_index
        string arxiv_id
        string title
        string summary
        datetime created_at
    }

    chat_web_source {
        integer id PK
        string session_id FK
        integer message_index
        string url
        string title
        string summary
        datetime created_at
    }

    chat_suggestion {
        integer id PK
        string session_id FK
        integer message_index
        string question
        datetime created_at
    }

    chat_image {
        integer id PK
        string session_id FK
        integer message_index
        binary image_data
        string media_type
        datetime created_at
    }

    research_gap_task {
        string task_id PK
        string mid FK
        string domain
        string query
        string status
        integer progress
        json result
        json translated_result
        string error_message
        datetime created_at
        datetime updated_at
    }

    notification {
        string id PK
        string mid FK
        string title
        string message
        string type
        string task_id
        boolean read
        datetime created_at
    }

    defense_arena_session {
        string session_id PK
        string member_id FK
        string file_name
        string file_path
        integer chunk_count
        datetime created_at
        datetime updated_at
        boolean is_saved
        json peer_review_result
        json hypothesis_result
        string final_report
        float defense_score
    }

    defense_arena_chunk {
        integer id PK
        string session_id FK
        integer chunk_index
        string text_chunk
        vector embedding
    }

    defense_history {
        integer id PK
        string session_id FK
        integer turn
        string question
        string answer
        integer score
        string feedback
        datetime created_at
    }

    paper_full_text_cache {
        string paper_id PK
        string title
        string full_text
        string domain
        string source
        boolean is_vectorized
        datetime created_at
    }

    member ||--o{ gem : "owns"
    member ||--o{ chat_session : "owns"
    member ||--o{ research_gap_task : "requests"
    member ||--o{ notification : "receives"
    member ||--o{ defense_arena_session : "initiates"

    gem ||--o{ gem_file : "owns (CASCADE)"
    chat_session ||--o{ chat_source : "has (CASCADE)"
    chat_session ||--o{ chat_web_source : "has (CASCADE)"
    chat_session ||--o{ chat_suggestion : "has (CASCADE)"
    chat_session ||--o{ chat_image : "has (CASCADE)"

    defense_arena_session ||--o{ defense_arena_chunk : "contains (CASCADE)"
    defense_arena_session ||--o{ defense_history : "records (CASCADE)"
```
