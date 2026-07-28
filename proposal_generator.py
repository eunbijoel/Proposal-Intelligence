"""
proposal_generator.py

RFP 분석 결과와 참고자료를 바탕으로
1) 우리 센터가 맡을 수 있는 역할 후보(최대 3개)
2) 선택한 역할에 대한 제안 초안
을 생성하는 모듈입니다.

모든 생성 결과는 아래 세 가지 표시 중 하나를 포함하도록 프롬프트에서 강제합니다.
- [자료 근거]  : 업로드한 문서에서 실제로 확인된 내용
- [AI 제안]    : 문서에는 없지만 LLM이 합리적으로 제안한 내용
- [확인 필요]  : 판단할 근거가 부족해 사용자가 채워야 하는 내용
"""

import json

from llm_client import generate_text, LLMConnectionError
from document_parser import chunks_to_text

NOT_FOUND = "확인 필요"


def suggest_roles(rfp_result: dict, reference_chunks: list[dict]) -> list[dict]:
    """
    RFP 분석 결과와 참고자료를 바탕으로 센터 역할 후보를 최대 3개 제안합니다.

    반환 형태:
    [
        {
            "role": "...",
            "reason": "...",
            "related_requirements": "...",
            "evidence": "...",
            "open_questions": "...",
        },
        ...
    ]

    reference_chunks가 비어 있으면(참고자료를 업로드하지 않았다면),
    evidence는 항상 "확인 필요"로 채워집니다 (없는 근거를 지어내지 않기 위함).
    """
    reference_text = chunks_to_text(reference_chunks) if reference_chunks else "(업로드된 참고자료 없음)"

    prompt = f"""당신은 공공 R&D 컨소시엄 제안서 작성을 돕는 보조 도구입니다.
아래 [RFP 분석 결과]와 [참고자료]를 바탕으로, 우리 센터가 맡을 수 있는 역할 후보를 최대 3개 제안하세요.

반드시 JSON 배열(리스트) 형식으로만 답하세요. 배열의 각 원소는 다음 키를 가진 객체입니다.
role, reason, related_requirements, evidence, open_questions (모두 문자열)

규칙:
- evidence 항목은 [참고자료]에 실제로 있는 내용만 적고, 파일명을 함께 표시하세요. 참고자료에 없으면 "{NOT_FOUND}" 라고 쓰세요.
- reason과 role은 RFP 요구사항과 연결지어 작성하되, 참고자료 근거가 없는 추론이면 문장 앞에 "[AI 제안]" 을 붙이세요.
- 판단할 정보가 부족하면 open_questions에 구체적으로 무엇을 확인해야 하는지 적으세요.
- 다른 기관(주관기관, 수요기업 등)의 역할은 확정적으로 쓰지 말고 "주관기관 작성 필요" 등으로 표시하세요.

[RFP 분석 결과]
{json.dumps(rfp_result, ensure_ascii=False, indent=2)}

[참고자료]
{reference_text}
"""

    try:
        raw_response = generate_text(prompt)
    except LLMConnectionError as e:
        return [{
            "role": "확인 필요 (LLM 연결 실패)",
            "reason": str(e),
            "related_requirements": NOT_FOUND,
            "evidence": NOT_FOUND,
            "open_questions": "llm_client.py 설정을 확인하세요.",
        }]

    return _parse_role_list(raw_response)


def generate_draft(rfp_result: dict, selected_role: dict, reference_chunks: list[dict]) -> dict:
    """
    선택한 역할 후보 하나를 기준으로 제안 초안을 생성합니다.

    반환 형태 (모든 값은 문자열이며, 문장마다 [자료 근거]/[AI 제안]/[확인 필요] 태그 포함):
    {
        "necessity": "...",
        "center_role": "...",
        "work_details": "...",
        "yearly_plan": "...",
        "deliverables": "...",
        "kpi_draft": "...",
        "consortium_role": "...",
        "expected_effects": "...",
        "open_questions": "...",
    }
    """
    reference_text = chunks_to_text(reference_chunks) if reference_chunks else "(업로드된 참고자료 없음)"

    prompt = f"""당신은 공공 R&D 컨소시엄 제안서의 "우리 센터 담당 파트" 초안을 작성하는 보조 도구입니다.
전체 컨소시엄 제안서를 완성하려 하지 말고, 우리 센터가 작성할 수 있는 부분만 작성하세요.

반드시 JSON 객체 형식으로만 답하세요. 키는 다음과 같습니다.
necessity, center_role, work_details, yearly_plan, deliverables, kpi_draft, consortium_role, expected_effects, open_questions
(모두 문자열이며, 여러 항목은 줄바꿈으로 구분한 하나의 문자열로 작성하세요)

규칙:
- 모든 문장 앞에 [자료 근거], [AI 제안], [확인 필요] 중 하나를 표시하세요.
- [자료 근거]로 표시하는 문장은 반드시 [참고자료]에 실제로 있는 내용이어야 하며, 가능하면 파일명을 함께 적으세요.
- 예산, 참여기업명, 정량 수치는 [참고자료]에 없으면 지어내지 말고 [확인 필요]로 표시하세요.
- 과거 제안서의 문장을 그대로 복사하지 말고 이번 RFP에 맞게 새로 작성하세요.
- 다른 기관의 역할은 "주관기관 작성 필요", "수요기업 확인 필요" 등으로 표시하세요.

[RFP 분석 결과]
{json.dumps(rfp_result, ensure_ascii=False, indent=2)}

[선택한 역할 후보]
{json.dumps(selected_role, ensure_ascii=False, indent=2)}

[참고자료]
{reference_text}
"""

    try:
        raw_response = generate_text(prompt)
    except LLMConnectionError as e:
        return _empty_draft(error=str(e))

    return _parse_draft(raw_response)


# ---------------------------------------------------
# 내부 helper 함수들
# ---------------------------------------------------

def _parse_role_list(raw_response: str) -> list[dict]:
    """LLM 응답(JSON 배열 문자열)을 파이썬 리스트로 파싱합니다."""
    cleaned = _strip_code_fence(raw_response)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, list):
            return parsed[:3]  # 최대 3개까지만 사용합니다.
    except json.JSONDecodeError:
        pass

    # 파싱 실패 시, 사용자가 원인을 알 수 있도록 원본 응답을 그대로 보여줍니다.
    return [{
        "role": "확인 필요 (응답 해석 실패)",
        "reason": "LLM 응답을 JSON으로 해석하지 못했습니다.",
        "related_requirements": NOT_FOUND,
        "evidence": NOT_FOUND,
        "open_questions": raw_response[:500],
    }]


def _parse_draft(raw_response: str) -> dict:
    """LLM 응답(JSON 객체 문자열)을 파이썬 dict로 파싱합니다."""
    cleaned = _strip_code_fence(raw_response)
    draft_keys = [
        "necessity", "center_role", "work_details", "yearly_plan",
        "deliverables", "kpi_draft", "consortium_role", "expected_effects",
        "open_questions",
    ]
    try:
        parsed = json.loads(cleaned)
        result = {key: parsed.get(key, NOT_FOUND) for key in draft_keys}
        return result
    except json.JSONDecodeError:
        result = _empty_draft(error="LLM 응답을 JSON으로 해석하지 못했습니다.")
        result["open_questions"] = raw_response[:500]
        return result


def _empty_draft(error: str = "") -> dict:
    """모든 항목이 확인 필요로 채워진 기본 초안을 만듭니다."""
    draft_keys = [
        "necessity", "center_role", "work_details", "yearly_plan",
        "deliverables", "kpi_draft", "consortium_role", "expected_effects",
        "open_questions",
    ]
    result = {key: f"[확인 필요] {error}" if error else NOT_FOUND for key in draft_keys}
    return result


def _strip_code_fence(text: str) -> str:
    """```json ... ``` 형태로 감싸진 응답에서 코드블록 기호를 제거합니다."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    return cleaned
