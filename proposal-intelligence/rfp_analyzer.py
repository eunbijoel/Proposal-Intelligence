"""
rfp_analyzer.py

공고문/RFP 텍스트를 분석해서 핵심 항목을 구조화된 형태(dict)로 뽑아내는 모듈입니다.

이 파일이 하는 일은 딱 한 가지입니다.
- RFP 텍스트 청크들을 받아서 -> 12개 항목이 채워진 딕셔너리를 돌려줍니다.

문서에서 찾지 못한 항목은 절대로 지어내지 않고 "확인 필요"로 채웁니다.
"""

import json

from llm_client import generate_text, LLMConnectionError
from document_parser import chunks_to_text

# RFP에서 뽑아낼 12개 항목입니다.
# 순서를 바꾸거나 항목을 추가하고 싶으면 이 리스트와 아래 프롬프트를 함께 수정하세요.
RFP_FIELDS = [
    "project_name",           # 사업명
    "purpose",                 # 사업 목적
    "organization",             # 발주기관 또는 전담기관
    "duration",                 # 사업기간
    "budget",                   # 예산 또는 지원 규모
    "mandatory_requirements",   # 필수 수행내용 (리스트)
    "tech_requirements",        # 기술 요구사항 (리스트)
    "kpi",                      # 정량적 성과지표 (리스트)
    "consortium_conditions",    # 참여기관 및 컨소시엄 조건
    "evaluation_criteria",      # 평가항목 (리스트)
    "submission_documents",     # 제출서류 (리스트)
    "notes",                    # 기타 주의사항
]

NOT_FOUND = "확인 필요"


def analyze_rfp(rfp_chunks: list[dict]) -> dict:
    """
    RFP 텍스트 청크 리스트를 받아서 구조화된 분석 결과(dict)를 반환합니다.

    반환되는 dict의 키는 RFP_FIELDS 와 동일합니다.
    LLM이 응답을 제대로 주지 못하거나 연결에 실패하면,
    모든 항목이 "확인 필요"로 채워진 결과를 반환하고
    result["error"] 에 오류 메시지를 담아 돌려줍니다.
    (화면이 죽지 않고, 사용자가 원인을 알 수 있도록 하기 위함입니다.)
    """
    source_text = chunks_to_text(rfp_chunks)

    prompt = _build_prompt(source_text)

    try:
        raw_response = generate_text(prompt)
    except LLMConnectionError as e:
        result = _empty_result()
        result["error"] = str(e)
        return result

    result = _parse_response(raw_response)
    return result


def _build_prompt(source_text: str) -> str:
    """RFP 분석용 프롬프트를 만듭니다."""
    field_list = ", ".join(RFP_FIELDS)
    return f"""당신은 공공 R&D 공고문을 분석하는 보조 도구입니다.
아래 [RFP 원문]에서만 근거를 찾아 다음 항목을 JSON 형식으로만 답하세요.
설명 문장이나 마크다운 코드블록 없이 JSON 객체 하나만 출력하세요.

항목: {field_list}

규칙:
- project_name, purpose, organization, duration, budget, consortium_conditions, notes 는 문자열입니다.
- mandatory_requirements, tech_requirements, kpi, evaluation_criteria, submission_documents 는 문자열의 리스트입니다.
- 원문에서 근거를 찾을 수 없는 항목은 절대로 추측하여 채우지 말고 정확히 "{NOT_FOUND}" 라는 문자열을 넣으세요.
- 리스트 항목도 근거가 없으면 ["{NOT_FOUND}"] 로 채우세요.
- 반드시 JSON 형식으로만 답하세요.

[RFP 원문]
{source_text}
"""


def _parse_response(raw_response: str) -> dict:
    """LLM 응답 문자열을 JSON으로 파싱합니다. 실패 시 안전한 기본값을 돌려줍니다."""
    cleaned = raw_response.strip()
    # 혹시 모델이 ```json ... ``` 형태로 감싸서 응답한 경우 제거합니다.
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        result = _empty_result()
        result["error"] = "LLM 응답을 JSON으로 해석하지 못했습니다. 원본 응답을 raw_response에 남겨둡니다."
        result["raw_response"] = raw_response
        return result

    # 누락된 항목은 "확인 필요"로 채워서 항상 12개 항목이 존재하도록 보장합니다.
    result = _empty_result()
    for field in RFP_FIELDS:
        if field in parsed and parsed[field]:
            result[field] = parsed[field]
    return result


def _empty_result() -> dict:
    """모든 항목이 '확인 필요'로 채워진 기본 결과를 만듭니다."""
    result = {}
    for field in RFP_FIELDS:
        if field in ("mandatory_requirements", "tech_requirements", "kpi",
                      "evaluation_criteria", "submission_documents"):
            result[field] = [NOT_FOUND]
        else:
            result[field] = NOT_FOUND
    return result
