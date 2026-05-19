# AI Prompt Platform

엑셀·CSV 파일을 자연어로 분석·처리하는 Streamlit 기반 AI 데이터 플랫폼.

핵심은 두 가지입니다.

1. **자동 모델 선택** — 사용자가 모델을 고르지 않습니다. 작업 유형을 분류한 뒤 적합한 모델이 자동으로 선택됩니다.
2. **3-Phase Tool 실행** — LLM이 직접 수치를 판단하지 않고, Python 도구가 실제 계산을 수행한 뒤 LLM이 결과만 설명합니다. 환각(hallucination)을 방지합니다.

---

## 핵심 구조: 자동 모델 선택

> **사용자가 직접 모델을 고르게 하면 안 됩니다.**  
> Model Manager는 모델 풀(pool)을 등록·관리하는 곳이지, 매 요청마다 모델을 고르는 UI가 아닙니다.

모든 AI 요청은 아래 [전체 파이프라인](#전체-파이프라인-현재-구현)을 따릅니다.

### 작업 유형 → 모델 매핑 (예시)

| Task Type | 트리거 예시 (사용자 표현) | 자동 선택 모델 | 이유 |
|---|---|---|---|
| `visualization` | "차트 만들어줘", "그래프 그려줘", "막대 차트로 보여줘" | `qwen3:14b` | 시각화·데이터 해석 균형 |
| `code_generation` | "Python 코드 생성해줘", "스크립트 짜줘", "pandas로 처리해" | `qwen2.5-coder:14b` | 코드 생성·실행 특화 |
| `long_form_report` | "긴 보고서 만들어줘", "전체 요약 보고서", "인사이트 정리해" | `gemma3:27b` | 장문 생성·한국어 서술 품질 |
| `data_analysis` | "집행률 계산해줘", "B열 합계", "두 파일 비교" | `qwen2.5:14b` | 표·수치 분석·한국어 |
| `quick_qa` | "이 열이 뭐야?", "몇 행이야?" | `gemma2` / `phi3` | 짧은 응답·저지연 |

표현이 달라도 Task Classifier가 **의도(intent)** 를 분류하면 동일한 모델이 선택됩니다.

```
"차트 그려줘"  ─┐
"그래프 보여줘" ├──→  visualization  →  qwen3:14b
"막대 그래프"  ─┘

"코드 짜줘"    ─┐
"스크립트 작성" ├──→  code_generation  →  qwen2.5-coder:14b
"pandas 처리"  ─┘
```

### 전체 파이프라인 (현재 구현)

플랫폼 전체(설정 → 파일 → AI 처리 → 결과)와 AI Prompt **질문 1회** 처리 흐름을 한 diagram에 정리했습니다.

```mermaid
flowchart TB
    subgraph SETUP["① 사전 설정 — Model Manager"]
        MM["pages/3_Model_Manager.py\nOllama pull · API 키"]
        MM --> CFG[("model_config.json")]
        CFG --> RM["role_models\nanalysis · code · precision"]
        CFG --> TM["task_models\n(작업 유형별 override)"]
        CFG --> OLL["ollama.models / openai / google"]
    end

    subgraph INGEST["② 파일 준비 — File Manager"]
        FM["pages/1_File_Manager.py\n업로드 · 미리보기"]
        FM --> UP[("uploads/\nxlsx · xls · csv")]
        FM --> SMART["_read_excel_smart\n병합셀 · 2행헤더 · 숫자변환\n헤더 col_N → 부모 헤더 이어받기"]
        FM --> AITAB["AI 분석 탭\ncall_ai_simple → task_router"]
    end

    subgraph AI["③ AI Prompt — 질문 1회 (pages/2_AI_Prompt.py)"]
        Q(["chat_input / 빠른 명령 / _pending\n대화 초기화 버튼(헤더)"])

        Q --> RP["route_for_prompt(prompt)"]
        RP --> CLS["classify_task\nvisualization · code_generation\ndata_analysis · long_form_report · quick_qa"]
        CLS --> RESOLVE["resolve_route\nrole_models → task_models\n→ DEFAULT → Ollama fallback\n→ CLOUD_FALLBACK"]
        RESOLVE --> AR["st.session_state auto_route\n사이드바 자동 모델 패널"]

        Q --> LOAD["load_files + _read_excel_smart"]
        LOAD --> P1["Phase 1 — call_planner\n실제 5행 샘플 포함 컨텍스트\nLLM → JSON Action Plan\n파일 미선택 시에도 UPLOAD_DIR 목록으로 실행"]

        P1 --> PLAN{"plan.steps\n있음?"}

        PLAN -->|Yes| P2["Phase 2 — TOOL_REGISTRY\n11개 Tool · Python만 실행\nLLM 개입 없음"]
        P2 --> CTX["ctx에 결과 누적\nlist_files · inspect · compare\naggregate · visualize · export …"]
        CTX --> P3["Phase 3 — stream_explainer\nTOOL_ROLES[첫 Tool] → role_models"]
        P3 --> SUG["generate_suggestions_ai\n추천 카드 최대 4개"]
        SUG --> RERUN["st.rerun()\n사이드바 모델 갱신"]

        PLAN -->|No| FB["Fallback — stream_ai_fallback\nfiles dict · result · save() 컨텍스트\ncode / code_generation 모델"]
        FB --> GEN["LLM Python 코드 생성\nfiles[파일명] 직접 접근\nresult = df 자동 테이블 표시"]
        GEN --> SAFE["AST 안전성 검사\n_check_code_safety()\n위험 모듈·함수 감지"]
        SAFE --> APR["승인 UI\n🟢 안전 / ⚠ 주의 배지\n실행하기 / 취소 버튼"]
        APR -->|승인| EXEC["extract_and_run_code\nfiles dict · save() · result\n30초 타임아웃 · 제한 builtins"]
        EXEC --> OUT2["차트 · outputs/ · result_df 테이블"]
    end

    subgraph OUT["④ 결과 · 이력"]
        P2 --> OUTDIR[("outputs/")]
        EXEC --> OUTDIR
        P2 --> LOG[("activity_log.json")]
        OUTDIR --> RS["pages/4_Results.py\n미리보기 · 다운로드 · Chat 저장"]
        LOG --> DASH["app.py Dashboard\n메트릭 · 최근 활동"]
    end

  SETUP -.->|resolve_route 읽기| RESOLVE
  INGEST --> Q
  UP --> LOAD
```

**Phase 2 Tool 목록 (11개)** — `TOOL_REGISTRY` in `2_AI_Prompt.py`

| 분류 | Tool |
|------|------|
| 파일 탐색 | `list_files`, `preview_file` |
| 분석·정제 | `inspect_column`, `compare_files`, `clean_table`, `aggregate`, `filter_rows`, `calculate_ratio`, `fill_missing` |
| 출력 | `visualize`, `export` |

```mermaid
flowchart LR
    subgraph P2DETAIL["Phase 2 — Tool Executor (결정론적)"]
        direction TB
        T1[list_files / preview_file]
        T2[inspect_column / compare_files]
        T3[aggregate / filter_rows / calculate_ratio]
        T4[clean_table / fill_missing]
        T5[visualize → chart_b64]
        T6[export → outputs/]
    end

    P1D["Phase 1 Planner\nclassify_task 모델"] --> P2DETAIL
    P2DETAIL --> P3D["Phase 3 Explainer\nTOOL_ROLES → role_models"]
```

### 설계 원칙

| 원칙 | 설명 |
|---|---|
| **사용자 무개입** | AI Prompt 사이드바에 모델 선택 UI를 두지 않음 |
| **작업 단위 라우팅** | 한 대화 안에서도 질문마다 task type이 달라지면 모델을 바꿀 수 있음 |
| **풀 기반 폴백** | 지정 모델이 미설치·VRAM 부족 시 같은 task type의 차순위 모델로 대체 |
| **Model Manager 역할** | Ollama/OpenAI/Google **연결·다운로드·풀 등록**만 담당 |

### 모델 결정 우선순위 (`resolve_route`)

`utils/task_router.py`가 아래 순서로 provider·model을 고릅니다.

1. `model_config.json` → **`role_models`** (Model Manager 역할 카드에서 저장)
2. **`task_models`** (작업 유형별 직접 지정, example config 참고)
3. **`DEFAULT_TASK_MODELS`** (코드 내 기본값 — Ollama 로컬)
4. 설치된 Ollama 목록에서 **fallback** 후보 순회
5. Ollama 불가 시 **`CLOUD_FALLBACK`** (OpenAI / Google API 키 필요)

### 구현 코드 맵

| 역할 | 파일 | 주요 심볼 |
|---|---|---|
| 작업 분류·모델 매핑·LLM 호출 | `utils/task_router.py` | `classify_task`, `resolve_route`, `route_for_prompt`, `call_with_route` |
| File Manager 등 단순 호출 | `utils/ai_caller.py` | `call_ai_simple`, `call_ai_for_task` |
| 채팅·3-Phase·보안 실행·사이드바 UI | `pages/2_AI_Prompt.py` | `call_planner`, `stream_explainer`, `_check_code_safety`, `extract_and_run_code` |
| 모델 풀 등록 UI | `pages/3_Model_Manager.py` | `save_role`, `ROLES`, `role_models` 저장 |
| 공통 CSS | `utils/styles.py` | `apply_global_css`, `empty_state` |
| Ollama VRAM 관리 | `utils/ollama_client.py` | `chat`, `iter_chat`, `unload_all_except` |

---

## 디렉토리 구조

```
ai-prompt-platform/
├── app.py                      # Dashboard
├── requirements.txt
├── model_config.json           # 모델 풀·API 키 (자동 생성)
├── model_config.example.json   # role_models / task_models 예시
├── activity_log.json           # 처리 이력 영속화 (자동 생성)
├── code_history.json           # Fallback 코드 히스토리 (자동 생성)
├── .streamlit/
│   └── config.toml             # 테마 설정
├── pages/
│   ├── 1_File_Manager.py       # 파일 업로드·미리보기·AI 분석 탭
│   ├── 2_AI_Prompt.py          # AI 대화 (자동 모델 + 3-Phase Tool + 보안 실행)
│   ├── 3_Model_Manager.py      # 모델 풀 등록·Ollama pull
│   └── 4_Results.py            # 결과 파일 관리·Chat 저장
├── utils/
│   ├── task_router.py          # ★ 작업 분류 + 모델 자동 선택
│   ├── ai_caller.py            # 공유 AI 호출 (task_router 래핑)
│   ├── activity_log.py         # 로그 영속화
│   ├── styles.py               # 공통 CSS (apply_global_css, empty_state)
│   ├── excel_processor.py      # 엑셀 처리
│   └── ollama_client.py        # Ollama HTTP·VRAM 관리
├── uploads/                    # 업로드 파일 저장소
└── outputs/                    # 결과 파일 저장소
```

---

## 설치 및 실행

```bash
pip install -r requirements.txt

# 최초 1회: 설정 파일 복사 (선택)
cp model_config.example.json model_config.json

streamlit run app.py
```

브라우저에서 **Model Manager** → Ollama 연결 및 역할별 모델(`analysis` / `code` / `precision`) 지정 후 **AI Prompt**에서 질문하면 자동 라우팅됩니다.

### 의존 패키지

| 패키지 | 용도 |
|---|---|
| streamlit ≥ 1.39 | UI 프레임워크 (`accept_file` 지원) |
| pandas ≥ 2.0 | 데이터 처리 |
| openpyxl ≥ 3.1 | 엑셀 읽기·쓰기 (병합 셀 처리 필수) |
| matplotlib ≥ 3.7 | 차트 생성 |
| plotly ≥ 5.0 | 인터랙티브 차트 (선택) |
| altair ≥ 5.0 | 대시보드 바 차트 |
| openai ≥ 1.0 | OpenAI API |
| requests ≥ 2.31 | Ollama HTTP 통신 |
| google-generativeai | Google Gemini (선택, requirements.txt 주석 해제) |

---

## 페이지별 기능

### Dashboard (`app.py`)

플랫폼 전체 현황을 한눈에 보여주는 메인 화면.

- **메트릭 카드 4개**: 업로드 파일 수 / 처리 건수 / 등록된 모델 수 / 토큰 사용량
- **모델 풀 상태**: 우상단 배지 — 미등록 시 경고 배너 (요청 시 자동 선택 불가)
- **최근 활동**: `activity_log.json` 기반, 상태 배지(uploaded / processed / saved / deleted / error)
- **주간 통계 차트**: 최근 7일 성공 처리 건수 Altair 바 차트
- **빠른 시작**: 모델 미설정 시 단계 안내 / 설정 완료 시 프롬프트 예시 6개

---

### File Manager (`pages/1_File_Manager.py`)

엑셀·CSV 파일 업로드 및 상세 미리보기.

- **파일 업로드**: 드래그&드롭 (xlsx / xls / csv), `uploads/` 저장
- **파일 목록**: 이름·날짜·크기 표시, 검색 필터, 체크박스 일괄 삭제
- **AI Prompt 연동**: 선택 파일을 AI Prompt 페이지로 바로 전송
- **미리보기 다이얼로그 — 4탭 구성**:
  - `원본`: openpyxl로 원본 시트 그대로 렌더링 (병합 셀 표시 포함)
  - `정리 데이터`: pandas로 읽은 분석용 테이블 + 컬럼별 통계 (숫자: 합계/평균/최솟값/최댓값 / 텍스트: 고유값 목록)
  - `AI 분석`: `call_ai_simple()` → `task_router`로 `data_analysis` 작업 유형 모델 자동 선택 (캐시)
  - `작업 로그`: 해당 파일에 대한 `activity_log.json` 이력 + 세션 코드 히스토리

---

### AI Prompt (`pages/2_AI_Prompt.py`)

핵심 기능. 자연어 질문 → **작업 분류·모델 자동 선택** → Python 도구 실행 → AI 결과 설명.

#### 아키텍처: Task Classification → Auto Model → 3-Phase Tools

요청마다 Task Classifier가 작업 유형을 판별하고, 그에 맞는 모델을 자동으로 로드합니다. 사용자는 모델명을 알 필요가 없습니다.

#### UI 기능

- **대화 초기화 버튼**: 페이지 헤더 우측 — 채팅 이력·토큰 카운터 전체 리셋
- **빠른 명령 버튼**: 파일 선택 시 8개 프리셋 (열 설명 / 집행률 계산 / 이상값 / 파일 비교 등)
- **후속 작업 제안 카드**: 응답 하단에 최대 4개 추천 (LLM 생성 + 정적 fallback), 클릭 시 자동 입력
- **코드 히스토리**: 사이드바 — Fallback 실행 코드 최근 8개, 클릭 시 재실행
- **자동 모델 패널**: 사이드바 읽기 전용 — 현재 질문에 선택된 모델명·작업 라벨 표시

#### 11개 Python Tool 함수

모든 Tool은 `(args: dict, ctx: dict, dfs: dict) -> dict` 시그니처를 공유.  
`ctx`에 이전 Tool 결과가 누적되어 다음 Tool이 참조 가능.

| Tool | 설명 | 주요 args |
|---|---|---|
| `list_files` | `uploads/` 파일 목록 + 행/열/텍스트 범위 통계 | (없음) |
| `preview_file` | 파일 데이터 미리보기 | `file`, `rows` (기본 20) |
| `inspect_column` | 열 상세 분석 (셀 주소 포함) | `file`, `column` |
| `compare_files` | 두 파일 diff (추가/제거/변경) | `file_a`, `file_b`, `key_col` |
| `clean_table` | 소계·빈 행 제거 | `file`, `remove_subtotals` |
| `aggregate` | 그룹별 집계 (sum/mean 등) | `file`, `group_by`, `value_col`, `func` |
| `filter_rows` | 조건 행 필터 | `file`, `column`, `condition`, `value` |
| `calculate_ratio` | 집행률·비율 계산 (키워드 자동 탐지) | `file`, `plan_col`, `exec_col`, `label_col` |
| `fill_missing` | 빈 셀 채우기 | `file`, `method` (zero/ffill/bfill/mean), `columns` |
| `visualize` | 막대/선/파이 차트 생성 | `file`, `chart_type`, `x`, `y` |
| `export` | 결과를 Excel/CSV로 저장 | `source_step`, `filename` |

`list_files` 반환 컬럼: `파일명 / 전체 행 / 전체 열 / 텍스트 열 / 숫자 열 / 데이터 있는 행 / 텍스트 입력 행 / 크기 / 상태`

#### Planner 컨텍스트 개선

`call_planner()`에 전달하는 파일 요약(`get_file_summaries`)이 실제 5행 샘플을 포함합니다.  
→ Planner LLM이 데이터 내용을 보고 더 정확한 Tool을 선택합니다.  
→ **파일이 선택되지 않은 상태**에서도 `UPLOAD_DIR` 목록을 Planner에 전달해 `list_files` 같은 도구가 동작합니다.

#### 엑셀 스마트 로딩 (`_read_excel_smart`)

`pd.read_excel()`의 한계를 openpyxl로 보완:

1. **병합 셀 해제**: 모든 병합 범위를 좌상단 값으로 채운 뒤 해제 → 병합으로 인한 NaN 방지
2. **헤더 col_N 문제 해결**: 가로 병합으로 생기는 보조 헤더 셀에 부모 헤더 값을 이어받아 `col_2`, `col_3` 대신 `비목분류_1`, `비목분류_2` 형식으로 처리
3. **2행 헤더 자동 감지**: 3번째 행에 숫자가 많고 2번째 행이 텍스트이면 1·2행을 합쳐 헤더 구성 (한국 공공 예산 엑셀 형식 대응). 부모 헤더도 이어받기 적용
4. **쉼표 포함 숫자 변환**: `'51,840,000'` → `51840000` (60% 이상 셀이 변환 가능하면 열 전체를 숫자형으로 변환)

#### 파일 구조 감사 (`_audit_file`)

파일 로드 시 자동 실행되는 품질 검사. 반환 항목:

| 항목 | 설명 |
|---|---|
| `filled_rows` | 1개 이상 셀이 채워진 행 수 |
| `text_filled_rows` | 텍스트 데이터가 있는 행 수 |
| `num_filled_rows` | 숫자 데이터가 있는 행 수 |
| `text_col_count` | 텍스트 타입 열 수 |
| `num_col_count` | 숫자 타입 열 수 |
| `warnings` | 소계 행 감지 / 미확인 헤더 / 빈 셀 비율 초과 |

#### Tool → LLM 역할 (`TOOL_ROLES`)

| 단계 | 모델 선택 방식 |
|---|---|
| **Planner** (`call_planner`) | `classify_task(질문)` → 작업 유형별 모델 |
| **Explainer** (`stream_explainer`) | 계획 **첫 번째 Tool**의 `TOOL_ROLES` → `role_models` |
| **Fallback** (`stream_ai_fallback`) | `code` / `code_generation` 고정 |

---

### 보안 & 안전 실행 (Fallback 코드 실행)

Fallback 경로에서 LLM이 생성한 코드를 실행하기 전에 두 단계 안전장치를 적용합니다.

#### 1단계: AST 안전성 검사 (`_check_code_safety`)

실행 전 코드를 파싱해 위험 패턴을 정적 분석합니다.

| 차단 항목 | 대상 |
|---|---|
| 위험 모듈 | `os`, `subprocess`, `shutil`, `socket`, `paramiko`, `pty`, `ctypes` |
| 위험 함수 | `eval`, `exec`, `compile`, `__import__` |
| 위험 메서드 | `system`, `popen`, `rmtree`, `remove`, `unlink`, `chmod` 등 |

결과는 `🟢 안전` 또는 `⚠ 주의 (N개 패턴 감지)` 배지로 표시됩니다.

#### 2단계: 사용자 승인 게이트 (`_render_code_approval`)

코드를 즉시 실행하지 않고 사용자 확인을 요청합니다.

```
AI 코드 생성 → AST 검사 → [실행하기 ▶] / [취소] 버튼 표시 → 사용자 클릭 후 실행
```

안전으로 판정된 코드는 "실행하기 ▶", 위험 패턴이 감지된 코드는 "그래도 실행" 버튼으로 표시해 시각적으로 경고합니다.

#### 안전 실행 환경 (`extract_and_run_code`)

승인 후 실행 시 제한된 샌드박스 환경을 사용합니다.

```python
exec_context = {
    "files":  {"파일명.xlsx": DataFrame, ...},  # 선택된 파일 미리 로드
    "save":   save_helper,                       # save(df, "결과.xlsx") → outputs/
    "result": None,                              # 여기에 저장하면 자동으로 테이블 표시
    "pd":     pandas,
    "plt":    matplotlib.pyplot,
    # open, eval, exec, input, getattr, setattr 차단
}
# 30초 POSIX 타임아웃 (무한루프 방지)
```

| 기능 | 설명 |
|---|---|
| `files` dict | 선택된 파일이 DataFrame으로 미리 로드 — `files["파일명.xlsx"]` 직접 접근 |
| `save(df, "결과.xlsx")` | DataFrame을 `outputs/`에 안전하게 저장하는 헬퍼 함수 |
| `result = df` | 이 변수에 DataFrame을 저장하면 실행 후 자동으로 테이블 + "Code executed successfully." 표시 |
| 제한 builtins | `open`, `eval`, `exec`, `input`, `getattr`, `setattr`, `delattr` 차단 |
| 30초 타임아웃 | POSIX SIGALRM — 초과 시 TimeoutError, 서버 보호 |

**Fallback 시스템 프롬프트 (LLM 지시사항 요약)**:
- `files["파일명"]`으로 DataFrame 접근 (`pd.read_excel()` 불필요)
- 결과 표시: `result = 최종_DataFrame`
- 파일 저장: `save(result, "결과파일명.xlsx")`
- `import` 금지 (pd, plt, io 등 이미 제공됨)

---

### Model Manager (`pages/3_Model_Manager.py`)

**모델 풀 등록·연결** 전용 페이지. 사용자가 매 요청마다 모델을 고르는 곳이 아닙니다.  
`save_role()`로 저장한 **`role_models`** 가 `task_router.resolve_route()`의 1순위 설정입니다.

| 역할 키 | 용도 | 권장 Ollama 모델 예 |
|---|---|---|
| `analysis` | Planner·표 분석·집계 | `qwen3:14b` |
| `code` | 차트·Fallback 코드 생성 | `qwen2.5-coder:14b` |
| `precision` | 장문 보고서·복잡 추론 | `gemma3:27b` |
| `embedding` | RAG·유사도 검색 (예정) | `nomic-embed-text` |

- **OpenAI / Google**: API 키·모델 풀 등록 (Ollama 없을 때 클라우드 폴백)
- **Ollama (local/remote)**: 자동 감지, `ollama pull`, 설치 목록 → `ollama.models`
- Ollama 모델 전환 시 VRAM 정리 (`unload_all_except`)

---

### Results (`pages/4_Results.py`)

결과 파일 관리 및 대화 내보내기.

- **Chat 저장**: 헤더 버튼 — AI Prompt 대화 전체를 Markdown으로 `outputs/`에 저장
- **Markdown 작성**: 새 메모·보고서 직접 작성
- **파일 목록**: 파일명·유형 배지(markdown/excel/csv)·날짜·크기
- **미리보기**: `.md` → 렌더링 / `.xlsx,.xls` → 데이터프레임(최대 50행) / `.csv` → 데이터프레임
- **다운로드 / 삭제** 버튼

---

## 데이터 흐름

```mermaid
flowchart LR
    MM["Model Manager\nrole_models 등록"] --> CFG[("model_config.json")]
    FM["File Manager"] --> UP[("uploads/")]
    UP --> AI["AI Prompt\nclassify_task → Tools → Explainer\n→ (Fallback) AST검사 → 승인 → exec"]
    CFG -.-> AI
    AI --> OUT[("outputs/")]
    AI --> LOG[("activity_log.json")]
    OUT --> RS["Results"]
    LOG --> DB["Dashboard"]
```

---

## 설계 철학: 자연어 → Task Classification → Auto Model → Tool 실행

### 기존 방식의 근본적 문제

초기 버전은 키워드 매칭 기반 **명령어 파서**였습니다.

```python
if "통합" in prompt or "합쳐" in prompt:
    merge_files()
elif "정렬" in prompt:
    sort_file()
```

표현이 조금만 달라져도 실패합니다. "5개 파일 합쳐줘"는 되지만, "B열 기준으로 정렬해줘"나 "3번째 시트만 추출해줘"처럼 사전에 등록하지 않은 요청은 전부 처리 불가능합니다. **질문이 새로 생길 때마다 코드를 추가**해야 하는 구조로, 확장성이 없습니다.

---

### 개선된 구조: 자연어 → Action Plan → Tool 실행

```
"빈 셀 메꿔줘"
"병합셀 채워줘"        →  LLM 해석  →  fill_missing 호출
"누락값 처리해줘"

"달라진 항목 알려줘"
"증감 분석해줘"        →  LLM 해석  →  compare_files 호출
"변경점 요약해줘"
```

```mermaid
flowchart TD
    U([무한한 자연어 표현]) --> TC

    TC["**Task Classification**\nvisualization / code_generation /\nlong_form_report / data_analysis / quick_qa"]
    TC --> SEL["**Model Auto-Select**\nqwen3:14b · qwen2.5-coder:14b · gemma3:27b …"]
    SEL --> LLM

    LLM["**LLM — Task Planner**\n선택된 모델이 JSON Action Plan 생성\n{\n  steps: [\n    { tool: 'compare_files', args: {...} },\n    { tool: 'visualize',    args: {...} }\n  ]\n}"]

    LLM --> EX["**Python Executor**\n유한한 Tool 집합에서 선택·실행\nLLM은 수치 계산에 관여하지 않음"]

    EX --> T1["inspect_column"]
    EX --> T2["compare_files"]
    EX --> T3["aggregate"]
    EX --> T4["calculate_ratio"]
    EX --> T5["visualize"]
    EX --> T6["export · ..."]

    T1 & T2 & T3 & T4 & T5 & T6 --> EXP["**LLM — Explainer**\nPython이 계산한 실제 결과만 받아\n한국어로 설명 (환각 없음)"]

    EXP --> R([응답 + 후속 제안 카드])
```

---

### 핵심 원칙: Tool 설계가 전부다

새 질문 유형이 생겨도 **Tool을 추가**하면 끝입니다. LLM이 알아서 새 Tool을 선택합니다.

| 원칙 | 설명 |
|---|---|
| **범용성** | Tool 하나가 넓은 범위의 질문을 커버해야 함 |
| **명확한 args** | LLM이 잘못 해석할 수 없도록 args 이름을 직관적으로 |
| **결정론적 실행** | Tool 내부는 순수 Python — 같은 입력은 항상 같은 결과 |
| **ctx 누적** | 이전 Tool 결과를 다음 Tool이 참조 가능하도록 연결 |

현재 구현된 11개 Tool로 처리 가능한 실무 요청 범위:

```mermaid
mindmap
  root((Tool))
    파일 탐색
      list_files\n업로드 목록·범위 통계
      preview_file\n데이터 미리보기
    데이터 조회
      inspect_column\n열 분석·셀 주소
      compare_files\n파일 간 diff
    데이터 정제
      clean_table\n소계·빈행 제거
      fill_missing\n빈 셀 채우기
    분석·계산
      aggregate\n그룹별 집계
      filter_rows\n조건 필터
      calculate_ratio\n집행률 계산
    출력
      visualize\n차트 생성
      export\nExcel·CSV 저장
```

---

### Fallback: 코드 생성 방식 (보안 강화)

Tool로 처리할 수 없는 요청(LLM이 Action Plan 생성에 실패한 경우)은 **코드 생성 방식**으로 전환됩니다.

```mermaid
flowchart LR
    FAIL["Planner 실패\n(JSON 생성 불가)"] --> GEN["LLM\nPython 코드 생성\nfiles·result·save() 컨텍스트"]
    GEN --> SAFE["AST 안전성 검사\n위험 모듈·함수 탐지"]
    SAFE --> APR["승인 UI\n🟢 안전 / ⚠ 주의"]
    APR --> EXEC["제한 샌드박스 실행\n30초 타임아웃\nbuiltins 제한"]
    EXEC --> OUT["result 테이블\n차트·파일 반환"]
```

파일의 실제 데이터(컬럼, 행 수, 샘플)를 시스템 프롬프트로 전달하므로 "샘플 데이터 기준" 가정 없이 동작합니다.  
LLM이 `files["파일명"]`으로 DataFrame에 직접 접근하고, `result = df`로 결과를 저장하면 자동으로 테이블이 표시됩니다.

---

## 지원 모델 (자동 선택 풀)

Model Manager에 등록해 두면 Task Classifier가 작업 유형에 맞게 자동으로 고릅니다.

| Provider | Task Type | 자동 선택 예시 | 비고 |
|---|---|---|---|
| Ollama (local) | `visualization` | `qwen3:14b` | 차트·그래프 |
| Ollama (local) | `code_generation` | `qwen2.5-coder:14b` | Fallback·스크립트 |
| Ollama (local) | `long_form_report` | `gemma3:27b` | 장문 보고서 |
| Ollama (local) | `data_analysis` | `qwen2.5:14b` | 표·집계·비교 |
| OpenAI | `data_analysis` (클라우드) | `gpt-4o-mini` | API 키 필요 |
| OpenAI | `long_form_report` (클라우드) | `gpt-4o` | 고품질 서술 |
| Google Gemini | `quick_qa` (클라우드) | `gemini-2.0-flash` | 저지연, 패키지 별도 설치 |
| Ollama (remote) | 전체 | 로컬과 동일 매핑 | GPU 서버 URL 지정 |

---

## 설정 (`model_config.json`)

최초 실행 시 자동 생성되거나, `model_config.example.json`을 복사해 시작할 수 있습니다.

```json
{
  "role_models": {
    "analysis":  { "provider": "ollama", "model": "qwen3:14b" },
    "code":      { "provider": "ollama", "model": "qwen2.5-coder:14b" },
    "precision": { "provider": "ollama", "model": "gemma3:27b" }
  },
  "task_models": {
    "visualization":    { "provider": "ollama", "model": "qwen3:14b" },
    "code_generation":  { "provider": "ollama", "model": "qwen2.5-coder:14b" },
    "long_form_report": { "provider": "ollama", "model": "gemma3:27b" },
    "data_analysis":    { "provider": "ollama", "model": "qwen2.5:14b" },
    "quick_qa":         { "provider": "ollama", "model": "gemma2" }
  },
  "ollama": { "host": "http://localhost:11434", "models": [] },
  "openai": { "key": "", "model": "gpt-4o" },
  "google": { "key": "", "model": "gemini-1.5-pro" }
}
```

- **`role_models`**: Model Manager 역할 카드와 1:1 대응 — AI Prompt Planner/Explainer가 우선 사용
- **`task_models`**: `classify_task()` 결과(task type)별 override
- **`ollama.models`**: `ollama list` 동기화 목록 — 미설치 모델은 fallback으로 대체

### `classify_task` 키워드 (요약)

| task type | 감지 키워드 예 |
|---|---|
| `code_generation` | 코드, python, pandas, 스크립트 |
| `visualization` | 차트, 그래프, 시각화, plot |
| `long_form_report` | 보고서, 리포트, 종합 분석, 브리핑 |
| `quick_qa` | 몇 행, 몇 열, 컬럼이 뭐 |
| `data_analysis` | 집행률, 집계, 비교, 필터 (기본값) |

키워드·가중치 전체 목록은 `utils/task_router.py`의 `_KEYWORDS`를 참고하세요.
