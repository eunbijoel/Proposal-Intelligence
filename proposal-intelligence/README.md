# Proposal Intelligence MVP

공고문/RFP를 업로드하면 문서를 분석하여, **우리 센터가 담당할 수 있는 제안 내용의 초안**을 만들어주는 간단한 웹 애플리케이션입니다.

전체 컨소시엄 제안서를 자동 완성하는 도구가 아니라, "우리 센터 담당 파트" 초안을 빠르게 잡아주는 것이 목적입니다.

## 프로젝트 목적

```
공고문/RFP 업로드 → 텍스트 추출 → RFP 핵심 요구사항 분석
→ 참고자료 확인 → 우리 센터 역할 후보 제안 → 담당 제안 내용 초안 생성
→ 화면에서 결과 확인/수정 → DOCX 또는 Markdown 다운로드
```

## 폴더/파일 설명


| 파일                      | 역할                                          |
| ----------------------- | ------------------------------------------- |
| `app.py`                | Streamlit 화면과 전체 실행 순서                      |
| `document_parser.py`    | PDF·DOCX에서 텍스트를 추출 (페이지/문단 위치 포함)           |
| `llm_client.py`         | LLM 호출 단일 진입점 (`generate_text()` 함수 하나만 사용) |
| `rfp_analyzer.py`       | RFP 텍스트를 12개 항목으로 구조화 분석                    |
| `proposal_generator.py` | 센터 역할 후보 3개, 제안 초안 생성                       |
| `document_exporter.py`  | 결과를 Markdown/DOCX 파일로 저장                    |
| `sample_data/`          | 테스트용 샘플 RFP 문서(`sample_rfp.docx`)           |
| `outputs/`              | 생성된 결과 파일이 저장되는 폴더                          |




## 설치 방법

Python 3.10 이상 권장.

```bash
cd proposal-intelligence
python -m venv venv
source venv/bin/activate   # Windows는 venv\Scripts\activate
pip install -r requirements.txt
```



## 실행 방법

```bash
streamlit run app.py
```

브라우저가 자동으로 열리지 않으면 터미널에 표시되는 `Local URL` (보통 [http://localhost:8501](http://localhost:8501)) 로 직접 접속하세요.



- PDF, DOCX 업로드 및 텍스트 추출 (페이지/문단 단위 출처 포함)
- RFP 12개 항목 구조화 분석 (`확인 필요` 자동 처리)
- 센터 역할 후보 최대 3개 제안
- 선택한 역할 기준 제안 초안 생성 (`[자료 근거]`/`[AI 제안]`/`[확인 필요]` 표시)
- 화면에서 초안 직접 수정
- Markdown, DOCX 다운로드
- Ollama 미연결 시에도 화면 흐름을 확인할 수 있는 MOCK_MODE



## 알려진 한계

- HWP, HWPX는 이번 버전에서 지원하지 않습니다 (안정적인 재사용 라이브러리가 없어 제외).
- 스캔된 이미지 PDF는 텍스트 추출이 되지 않습니다 (OCR 미지원).
- 표(테이블) 추출은 DOCX만 지원하며, PDF 표는 본문 텍스트로만 섞여 추출될 수 있습니다.
- 위치 정보는 "파일명 + 페이지/문단" 수준의 단순 표시이며, 정확한 좌표 기반 위치는 아닙니다.
- 벡터 검색을 사용하지 않으므로, 참고자료가 매우 길면 앞부분 일부만 프롬프트에 포함됩니다 (`document_parser.chunks_to_text`의 `max_chars` 제한).
- LLM 응답이 JSON 형식을 지키지 않으면 파싱에 실패할 수 있습니다 (이 경우 오류 메시지와 원본 응답 일부를 화면에 표시합니다).
- 사용자 계정, 데이터베이스, 자동 제출 기능은 없습니다.



## 이후 추가하기 좋은 기능

- HWP/HWPX 파서 연결 (안정적인 라이브러리 확보 시)
- PDF 표 추출 (예: `pdfplumber`)
- 스캔 PDF OCR 지원
- 긴 문서를 위한 청크 검색(임베딩 기반) 도입
- 프롬프트/응답 로그 저장 기능
- 여러 RFP를 비교 분석하는 기능

