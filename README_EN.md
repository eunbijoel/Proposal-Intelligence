# Proposal Intelligence

**Generate proposal drafts quickly from your existing materials** — with the help of LLM.

> [한국어](README.md) | [English](README_EN.md)

### What it does

Upload an RFP (Request for Proposal) along with your organization's existing materials (past proposals, capability statements, etc.).  
The LLM analyzes the RFP requirements, finds supporting evidence from your materials, and generates a **proposal draft**.

- RFP → Structured requirement extraction
- Reference docs → Evidence matching
- Combined → Draft proposal aligned to format

> This is not a full proposal auto-writer.  
> It helps you **quickly draft your team's section** based on real data.



### How it works

```
RFP upload → Text extraction → Requirement analysis (LLM)
                                        ↓
Reference upload → Text extraction → Evidence matching
                                        ↓
              Role suggestions → Draft generation (LLM) → Edit → Download
```



### Tech Stack

- **Frontend**: Streamlit
- **LLM**: Ollama (local) — currently using `gemma4`
- **Document Parsing**: pypdf, python-docx
- **Export**: Markdown, DOCX



### Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```



### File Structure


| File                    | Role                               |
| ----------------------- | ---------------------------------- |
| `app.py`                | Streamlit UI + orchestration       |
| `document_parser.py`    | PDF/DOCX text extraction           |
| `llm_client.py`         | Single entry point for LLM calls   |
| `rfp_analyzer.py`       | RFP structured analysis            |
| `proposal_generator.py` | Role suggestion + draft generation |
| `document_exporter.py`  | Export to file                     |




### Current Limitations

- Supports PDF and DOCX only (no HWP or scanned PDFs)
- Long documents are partially analyzed (front-truncated)
- LLM response format may be unstable (improving)



### Roadmap

- [ ] Template-based output formatting
- [ ] PDF table extraction
- [ ] Prompt stabilization (JSON response quality)
- [ ] Better handling of long documents (chunk retrieval)