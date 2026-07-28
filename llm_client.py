"""
llm_client.py

프로젝트 전체에서 LLM을 호출하는 유일한 통로입니다.
다른 파일(rfp_analyzer.py, proposal_generator.py)은 절대로
Ollama나 다른 API를 직접 호출하지 않고, 이 파일의 generate_text() 함수만 사용합니다.

이렇게 한 곳에서만 LLM을 호출하게 만들면, 나중에 모델을 바꾸거나
다른 API(OpenAI, Anthropic 등)로 교체할 때 이 파일 하나만 고치면 됩니다.

=====================================================
설정 변경은 아래 "설정값" 부분만 수정하면 됩니다.
=====================================================
"""

import json
import urllib.request
import urllib.error

# ---------------------------------------------------
# 설정값 (여기만 바꾸면 됩니다)
# ---------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "gemma4:e4b"  # 현재 로컬에 설치된 gemma4 모델 기준
REQUEST_TIMEOUT_SEC = 120

# MOCK_MODE가 True이면 실제 LLM을 호출하지 않고,
# 화면 흐름을 테스트할 수 있도록 가짜(더미) 응답을 돌려줍니다.
# 실제 LLM(Ollama 등)을 연결했다면 반드시 False로 바꿔서 사용하세요.
MOCK_MODE = False


class LLMConnectionError(Exception):
    """LLM 서버에 연결할 수 없을 때 발생하는 예외입니다."""
    pass


def generate_text(prompt: str) -> str:
    """
    LLM에 프롬프트를 전달하고 응답 텍스트를 반환합니다.

    MOCK_MODE가 True이면 실제 호출 없이 안내용 더미 텍스트를 반환합니다.
    (Ollama가 설치되지 않은 환경에서도 화면 동작을 확인할 수 있게 하기 위함입니다.)

    실패 시에는 빈 문자열이나 가짜 데이터를 만들지 않고,
    LLMConnectionError를 그대로 발생시킵니다.
    호출하는 쪽(app.py)에서 이 예외를 잡아 사용자에게 안내 메시지를 보여줘야 합니다.
    """
    if MOCK_MODE:
        return _mock_response(prompt)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SEC) as response:
            body = json.loads(response.read().decode("utf-8"))
            return body.get("response", "")
    except urllib.error.URLError as e:
        raise LLMConnectionError(
            f"Ollama 서버({OLLAMA_URL})에 연결할 수 없습니다. "
            f"Ollama가 실행 중인지, MODEL_NAME이 올바른지 확인하세요. 원본 오류: {e}"
        )
    except Exception as e:
        raise LLMConnectionError(f"LLM 호출 중 알 수 없는 오류가 발생했습니다: {e}")


def _mock_response(prompt: str) -> str:
    """
    MOCK_MODE 전용 더미 응답 생성 함수입니다.
    prompt 안에 포함된 특정 키워드를 보고 대략적인 형식만 맞춰서 돌려줍니다.
    실제 분석 품질과는 무관하며, 오직 "화면이 끊기지 않고 동작하는지" 확인용입니다.
    """
    # 프롬프트 안의 고유한 표시(marker)를 기준으로 어떤 함수가 호출했는지 구분합니다.
    # 순서가 중요합니다: "[선택한 역할 후보]"는 "역할 후보"라는 글자를 포함하므로
    # generate_draft 판단을 먼저 확인해야 합니다.
    if "[RFP 원문]" in prompt:
        # rfp_analyzer.analyze_rfp() 에서 호출한 경우
        return json.dumps({
            "project_name": "확인 필요",
            "purpose": "확인 필요",
            "organization": "확인 필요",
            "duration": "확인 필요",
            "budget": "확인 필요",
            "mandatory_requirements": ["확인 필요 (MOCK_MODE: 실제 LLM 미연결 상태입니다)"],
            "tech_requirements": ["확인 필요"],
            "kpi": ["확인 필요"],
            "consortium_conditions": "확인 필요",
            "evaluation_criteria": ["확인 필요"],
            "submission_documents": ["확인 필요"],
            "notes": "MOCK_MODE가 켜져 있어 실제 분석이 수행되지 않았습니다. llm_client.py에서 MOCK_MODE=False로 바꾸고 Ollama를 연결하세요.",
        }, ensure_ascii=False)

    if "[선택한 역할 후보]" in prompt:
        # proposal_generator.generate_draft() 에서 호출한 경우
        return json.dumps({
            "necessity": "[확인 필요] MOCK_MODE 상태입니다. llm_client.py에서 MOCK_MODE=False로 바꾸고 Ollama를 연결하세요.",
            "center_role": "[AI 제안] 예시 텍스트 (MOCK_MODE)",
            "work_details": "[확인 필요]",
            "yearly_plan": "[확인 필요]",
            "deliverables": "[확인 필요]",
            "kpi_draft": "[확인 필요]",
            "consortium_role": "[확인 필요]",
            "expected_effects": "[확인 필요]",
            "open_questions": "MOCK_MODE를 해제하고 실제 LLM을 연결하면 실제 초안이 생성됩니다.",
        }, ensure_ascii=False)

    if "역할 후보를 최대" in prompt:
        # proposal_generator.suggest_roles() 에서 호출한 경우
        return json.dumps([
            {
                "role": "[AI 제안] 예시 역할명 (MOCK_MODE)",
                "reason": "실제 LLM 미연결 상태의 더미 데이터입니다.",
                "related_requirements": "확인 필요",
                "evidence": "확인 필요",
                "open_questions": "MOCK_MODE를 해제하고 실제 LLM을 연결하세요.",
            }
        ], ensure_ascii=False)

    # 그 외 알 수 없는 프롬프트에 대한 기본 더미 응답
    return (
        "[AI 제안] (MOCK_MODE 더미 응답)\n"
        "llm_client.py 의 MOCK_MODE 값을 False로 바꾸고 Ollama를 연결하면 "
        "실제 분석/생성 결과가 이 자리에 표시됩니다."
    )
