# Proposal Intelligence

**기존 자료를 기반으로 제안서 초안을 작성해주는 Tool (LLM)**

> [한국어](README.md) | [English](README_EN.md)

### 활용 방법

공고문(RFP)과 우리 조직의 기존 자료(과거 제안서, 기술 역량 문서 등)를 함께 업로드하면,  
LLM이 RFP 요구사항을 분석하고, 기존 자료에서 근거를 찾아 **제안 초안**을 작성해 줍니다.

- 공고문 → 핵심 요구사항 구조화
- 기존 자료 → 근거 추출 및 매칭
- 두 가지를 결합 → 포맷에 맞는 제안 초안 생성

> 전체 제안서를 자동 완성하는 게 아니라,  
> **"우리 파트 초안을 빠르게 잡아주는 것"**이 목적입니다.

### 동작 흐름

```
RFP 업로드 → 텍스트 추출 → 요구사항 분석(LLM)
                                    ↓
참고자료 업로드 → 텍스트 추출 → 근거 매칭
                                    ↓
              역할 후보 제안 → 초안 생성(LLM) → 편집 → 다운로드
```



### 기술 스택

- **Frontend**: Streamlit
- **LLM**: Ollama (local) — 현재 `gemma4` 사용
- **문서 파싱**: pypdf, python-docx
- **출력 형식**: Markdown, DOCX



### 빠른 시작

```bash
pip install -r requirements.txt
streamlit run app.py
```



### 파일 구조


| 파일                      | 역할                   |
| ----------------------- | -------------------- |
| `app.py`                | Streamlit UI + 실행 흐름 |
| `document_parser.py`    | PDF/DOCX 텍스트 추출      |
| `llm_client.py`         | LLM 호출 단일 진입점        |
| `rfp_analyzer.py`       | RFP 구조화 분석           |
| `proposal_generator.py` | 역할 추천 + 초안 생성        |
| `document_exporter.py`  | 결과 파일 저장             |




### 현재 한계

- PDF, DOCX만 지원 (HWP/스캔 PDF 미지원)
- 긴 문서는 앞부분만 분석에 반영됨
- LLM 응답 형식이 불안정할 수 있음 (개선 중)



### 로드맵

- [ ] 제안서 템플릿 기반 출력 포맷 정렬
- [ ] PDF 표 추출
- [ ] 프롬프트 안정화 (JSON 응답 품질)
- [ ] 긴 문서 처리 개선 (청크 검색)