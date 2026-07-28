"""
app.py

Proposal Intelligence MVP의 메인 화면입니다.
이 파일은 화면 구성과 "전체 실행 순서"만 담당합니다.
실제 분석/생성 로직은 다른 파일(rfp_analyzer.py, proposal_generator.py 등)에서 가져다 씁니다.

실행 방법:
    streamlit run app.py

전체 흐름:
    1. 공고문/RFP 업로드 (필수) + 참고자료 업로드 (선택)
    2. [RFP 분석] 버튼 -> RFP 핵심 항목 추출
    3. 역할 후보 3개 확인 -> 하나 선택
    4. [제안 초안 생성] 버튼 -> 초안 생성
    5. 화면에서 초안 직접 수정
    6. DOCX 또는 Markdown 다운로드
"""

import tempfile
from pathlib import Path

import streamlit as st

from document_parser import extract_text
from rfp_analyzer import analyze_rfp, RFP_FIELDS
from proposal_generator import suggest_roles, generate_draft
from document_exporter import build_markdown, export_markdown, export_docx, DRAFT_LABELS

st.set_page_config(page_title="Proposal Intelligence MVP", layout="wide")

# -----------------------------------------------------
# session_state 초기화
# 화면이 다시 그려져도 이전 단계의 결과가 사라지지 않도록
# streamlit의 session_state에 결과를 저장해 둡니다.
# -----------------------------------------------------
if "rfp_result" not in st.session_state:
    st.session_state.rfp_result = None
if "role_candidates" not in st.session_state:
    st.session_state.role_candidates = None
if "selected_role" not in st.session_state:
    st.session_state.selected_role = None
if "draft" not in st.session_state:
    st.session_state.draft = None
if "rfp_chunks" not in st.session_state:
    st.session_state.rfp_chunks = []
if "reference_chunks" not in st.session_state:
    st.session_state.reference_chunks = []


st.title("📄 Proposal Intelligence")
st.caption("공고문/RFP를 업로드하면 우리 센터가 담당할 수 있는 제안 내용의 초안을 만들어 드립니다.")


def save_uploaded_file(uploaded_file) -> str:
    """업로드된 파일을 임시 폴더에 저장하고 경로를 반환합니다."""
    suffix = Path(uploaded_file.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        return tmp.name


def parse_uploaded_files(uploaded_files) -> list[dict]:
    """업로드된 여러 파일을 모두 텍스트 청크로 변환해서 하나의 리스트로 합칩니다."""
    all_chunks = []
    for uploaded_file in uploaded_files:
        tmp_path = save_uploaded_file(uploaded_file)
        chunks = extract_text(tmp_path)
        if not chunks:
            st.warning(f"'{uploaded_file.name}' 파일은 이번 버전에서 지원하지 않는 형식이거나 처리에 실패했습니다. "
                       f"(현재 PDF, DOCX만 지원합니다)")
        all_chunks.extend(chunks)
    return all_chunks


# =======================================================
# 화면 1: 파일 업로드
# =======================================================
st.header("1️⃣ 자료 업로드")

col1, col2 = st.columns(2)

with col1:
    st.subheader("공고문 또는 RFP (필수)")
    rfp_files = st.file_uploader(
        "PDF 또는 DOCX 파일을 업로드하세요",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key="rfp_uploader",
    )

with col2:
    st.subheader("참고자료 (선택)")
    st.caption("과거 유사 제안서, 우리 센터 기술자료, 기존 보고서/사업계획서, 제안서 양식 등")
    reference_files = st.file_uploader(
        "PDF 또는 DOCX 파일을 업로드하세요",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        key="reference_uploader",
    )

if rfp_files:
    st.success(f"공고문/RFP {len(rfp_files)}개 업로드됨: " + ", ".join(f.name for f in rfp_files))
if reference_files:
    st.info(f"참고자료 {len(reference_files)}개 업로드됨: " + ", ".join(f.name for f in reference_files))

st.divider()

# =======================================================
# 화면 2: RFP 분석
# =======================================================
st.header("2️⃣ RFP 분석")

if st.button("RFP 분석 시작", type="primary", disabled=not rfp_files):
    with st.spinner("RFP 문서를 읽고 분석하는 중입니다..."):
        st.session_state.rfp_chunks = parse_uploaded_files(rfp_files)
        st.session_state.reference_chunks = parse_uploaded_files(reference_files) if reference_files else []
        st.session_state.rfp_result = analyze_rfp(st.session_state.rfp_chunks)
        # 새로 분석했으니 이전 단계 결과는 초기화합니다.
        st.session_state.role_candidates = None
        st.session_state.selected_role = None
        st.session_state.draft = None

if not rfp_files:
    st.caption("공고문/RFP를 먼저 업로드해야 분석 버튼을 누를 수 있습니다.")

if st.session_state.rfp_result:
    result = st.session_state.rfp_result

    if result.get("error"):
        st.error(f"분석 중 문제가 발생했습니다: {result['error']}")

    with st.expander("RFP 분석 결과 보기", expanded=True):
        field_labels = {
            "project_name": "사업명", "purpose": "사업 목적", "organization": "발주/전담기관",
            "duration": "사업기간", "budget": "예산", "mandatory_requirements": "필수 수행내용",
            "tech_requirements": "기술 요구사항", "kpi": "정량적 성과지표",
            "consortium_conditions": "참여기관/컨소시엄 조건", "evaluation_criteria": "평가항목",
            "submission_documents": "제출서류", "notes": "기타 주의사항",
        }
        for field in RFP_FIELDS:
            label = field_labels.get(field, field)
            value = result.get(field, "확인 필요")
            if isinstance(value, list):
                st.markdown(f"**{label}**")
                for item in value:
                    st.markdown(f"- {item}")
            else:
                st.markdown(f"**{label}**: {value}")

st.divider()

# =======================================================
# 화면 3: 센터 역할 및 제안 초안
# =======================================================
st.header("3️⃣ 센터 역할 및 제안 초안")

can_suggest_roles = st.session_state.rfp_result is not None

if st.button("센터 역할 후보 추천받기", disabled=not can_suggest_roles):
    with st.spinner("참고자료와 비교하여 역할 후보를 찾는 중입니다..."):
        st.session_state.role_candidates = suggest_roles(
            st.session_state.rfp_result, st.session_state.reference_chunks
        )
        st.session_state.selected_role = None
        st.session_state.draft = None

if not can_suggest_roles:
    st.caption("먼저 RFP 분석을 완료해야 역할 후보를 추천받을 수 있습니다.")

if st.session_state.role_candidates:
    roles = st.session_state.role_candidates
    role_labels = [f"{i+1}. {r.get('role', '확인 필요')}" for i, r in enumerate(roles)]

    for i, role in enumerate(roles):
        with st.container(border=True):
            st.markdown(f"**{role_labels[i]}**")
            st.markdown(f"- 추천 이유: {role.get('reason', '확인 필요')}")
            st.markdown(f"- 관련 RFP 요구사항: {role.get('related_requirements', '확인 필요')}")
            st.markdown(f"- 근거 자료: {role.get('evidence', '확인 필요')}")
            st.markdown(f"- 확인 필요 사항: {role.get('open_questions', '확인 필요')}")

    selected_idx = st.radio(
        "제안 초안을 작성할 역할을 선택하세요",
        options=range(len(roles)),
        format_func=lambda i: role_labels[i],
    )

    if st.button("제안 초안 생성", type="primary"):
        with st.spinner("제안 초안을 작성하는 중입니다..."):
            st.session_state.selected_role = roles[selected_idx]
            st.session_state.draft = generate_draft(
                st.session_state.rfp_result,
                st.session_state.selected_role,
                st.session_state.reference_chunks,
            )

st.divider()

# =======================================================
# 화면 4: 결과 편집 및 다운로드
# =======================================================
st.header("4️⃣ 결과 편집 및 다운로드")

if st.session_state.draft:
    st.caption("아래 내용을 직접 수정한 뒤 다운로드하세요. `[자료 근거]` `[AI 제안]` `[확인 필요]` 표시를 참고하세요.")

    edited_draft = {}
    for key, label in DRAFT_LABELS.items():
        edited_draft[key] = st.text_area(
            label,
            value=str(st.session_state.draft.get(key, "확인 필요")),
            height=120,
            key=f"edit_{key}",
        )
    st.session_state.draft = edited_draft

    st.subheader("다운로드")
    dl_col1, dl_col2 = st.columns(2)

    markdown_text = build_markdown(
        st.session_state.rfp_result, st.session_state.selected_role, st.session_state.draft
    )

    with dl_col1:
        st.download_button(
            "📥 Markdown 다운로드 (.md)",
            data=markdown_text,
            file_name="proposal_draft.md",
            mime="text/markdown",
        )

    with dl_col2:
        if st.button("📥 DOCX 파일 만들기"):
            docx_path = export_docx(
                st.session_state.rfp_result, st.session_state.selected_role, st.session_state.draft
            )
            with open(docx_path, "rb") as f:
                st.download_button(
                    "생성된 DOCX 다운로드",
                    data=f.read(),
                    file_name=Path(docx_path).name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
else:
    st.caption("먼저 제안 초안을 생성해야 편집·다운로드할 수 있습니다.")
