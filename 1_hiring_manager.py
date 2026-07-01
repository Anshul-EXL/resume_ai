import streamlit as st
import time
import pandas as pd
import json
import requests
import uuid
import utils.storage as storage # form the utils folder
from datetime import datetime


# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Hiring Manager - TalentMatch AI",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# ENTERPRISE AI EXTRACTION ENGINE (OLLAMA)
# ==========================================
class OllamaExtractionEngine:
    OLLAMA_URL = "http://localhost:11434/api/generate"
    DEFAULT_MODEL = "deepseek-r1:8b" 

    SYSTEM_PROMPT = """You are an Enterprise Talent Intelligence Engine.
Analyze this Job Description.
Extract every possible hiring attribute and return ONLY valid JSON.
Provide explainability, confidence scores (0.0 to 1.0), and the source text snippet for EVERY extracted field.
If something is not available, return null for the value.
Do not hallucinate.

Extract exactly matching this schema:
{
  "company_information": {
    "company_name": {"value": "", "confidence": 0.0, "source": ""},
    "industry": {"value": "", "confidence": 0.0, "source": ""},
    "company_size": {"value": "", "confidence": 0.0, "source": ""}
  },
  "position_details": {
    "job_title": {"value": "", "confidence": 0.0, "source": ""},
    "department": {"value": "", "confidence": 0.0, "source": ""},
    "job_level": {"value": "", "confidence": 0.0, "source": ""},
    "employment_type": {"value": "", "confidence": 0.0, "source": ""},
    "work_mode": {"value": "", "confidence": 0.0, "source": ""},
    "location": {"value": "", "confidence": 0.0, "source": ""},
    "notice_period": {"value": "", "confidence": 0.0, "source": ""}
  },
  "experience": {
    "minimum_years": {"value": "", "confidence": 0.0, "source": ""},
    "summary": {"value": "", "confidence": 0.0, "source": ""}
  },
  "education": {
    "degree_required": {"value": "", "confidence": 0.0, "source": ""}
  },
  "job_summary": {"value": "", "confidence": 0.0, "source": ""},
  "responsibilities": [
    {"value": "", "confidence": 0.0, "source": ""}
  ],
  "mandatory_skills": [
    {"name": "", "confidence": 0.0, "source": ""}
  ],
  "preferred_skills": [
    {"name": "", "confidence": 0.0, "source": ""}
  ],
  "technology_stack": {
    "programming": [{"name": "", "confidence": 0.0, "source": ""}],
    "cloud_platforms": [{"name": "", "confidence": 0.0, "source": ""}],
    "databases": [{"name": "", "confidence": 0.0, "source": ""}],
    "frameworks": [{"name": "", "confidence": 0.0, "source": ""}],
    "tools": [{"name": "", "confidence": 0.0, "source": ""}]
  },
  "soft_skills": [
    {"name": "", "confidence": 0.0, "source": ""}
  ],
  "hiring_risks": [
    {"value": "", "confidence": 0.0, "source": ""}
  ],
  "interview_questions": {
    "technical": [{"value": "", "confidence": 0.0, "source": ""}],
    "behavioral": [{"value": "", "confidence": 0.0, "source": ""}]
  },
  "score_weights": {
    "mandatory_skills": 40,
    "experience": 20,
    "preferred_skills": 15,
    "education": 5,
    "domain_knowledge": 10,
    "semantic_match": 10
  }
}"""

    @classmethod
    def extract(cls, jd_text):
        prompt = f"{cls.SYSTEM_PROMPT}\n\nJOB DESCRIPTION:\n{jd_text}"
        
        payload = {
            "model": cls.DEFAULT_MODEL,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1 
            }
        }
        
        try:
            response = requests.post(cls.OLLAMA_URL, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            return json.loads(result.get("response", "{}"))
        except requests.exceptions.RequestException as e:
            st.error(f"Connection error to Ollama: {e}")
            return cls._get_fallback_json()
        except json.JSONDecodeError as e:
            st.error(f"Failed to parse JSON from Ollama: {e}")
            return cls._get_fallback_json()

    @classmethod
    def _get_fallback_json(cls):
        start_idx = cls.SYSTEM_PROMPT.find("{")
        if start_idx != -1:
            return json.loads(cls.SYSTEM_PROMPT[start_idx:])
        return {}

# ==========================================
# STATE INITIALIZATION
# ==========================================
def init_state():
    if 'step' not in st.session_state:
        st.session_state.step = 1
    if 'raw_blueprint' not in st.session_state:
        st.session_state.raw_blueprint = {}
    if 'flat_blueprint' not in st.session_state:
        st.session_state.flat_blueprint = {}
    if 'selected_persona_id' not in st.session_state:
        st.session_state.selected_persona_id = None

init_state()

# ==========================================
# HELPER FUNCTIONS (EXTRACTORS)
# ==========================================
def set_step(step_num):
    st.session_state.step = step_num

def run_ai_analysis(jd_text):
    with st.spinner("TalentMatch AI is intelligently extracting rich attributes via AI..."):
        start_time = time.time()
        extracted_data = OllamaExtractionEngine.extract(jd_text)
        
        elapsed = time.time() - start_time
        if elapsed < 1.5:
            time.sleep(1.5 - elapsed)
            
        st.session_state.raw_blueprint = extracted_data
        st.session_state.flat_blueprint = {} # Reset flat state for editing
        st.session_state.step = 2

def save_current_persona():
    new_persona = st.session_state.flat_blueprint.copy()

    persona_id = storage.save_persona(new_persona)

    st.session_state.selected_persona_id = persona_id

    st.toast(
        f"Persona '{new_persona.get('job_title','Untitled')}' saved successfully!",
        icon="✅"
    )

    set_step(3)

def u_val(field_obj, default=""):
    """Unpack value from rich object"""
    if isinstance(field_obj, dict):
        val = field_obj.get("value")
        return str(val) if val is not None else default
    return str(field_obj) if field_obj else default

def u_help(field_obj):
    """Unpack explainability tooltip from rich object"""
    if isinstance(field_obj, dict):
        conf = field_obj.get("confidence", "N/A")
        src = field_obj.get("source", "N/A")
        return f"AI Confidence: {conf}\nSource: \"{src}\""
    return "Manually entered or unverified"

def u_list(list_obj, key="name"):
    """Unpack list of rich objects into list of strings"""
    if not isinstance(list_obj, list):
        return []
    res = []
    for item in list_obj:
        if isinstance(item, dict):
            val = item.get(key) or item.get("value")
            if val: res.append(str(val))
        elif isinstance(item, str) and item:
            res.append(item)
    return res

# ==========================================
# UI COMPONENTS
# ==========================================
def render_header():
    st.title("TalentMatch AI")
    st.markdown("### AI-Powered Resume Intelligence Platform")
    st.markdown("---")
    
    c1, c2 = st.columns([4, 1])
    with c1:
        st.markdown("#### Create Hiring Request")
    with c2:
        st.metric("Saved Personas", len(storage.load_personas()))
    
    cols = st.columns(3)
    steps = [
        ("Step 1", "Job Description Input"),
        ("Step 2", "AI Analysis & Validation"),
        ("Step 3", "Select & Upload Resumes")
    ]
    
    for i, (col, (step_label, step_desc)) in enumerate(zip(cols, steps)):
        with col:
            step_num = i + 1
            if st.session_state.step == step_num:
                st.info(f"**{step_label}**: {step_desc}")
            elif st.session_state.step > step_num:
                st.success(f"**{step_label}**: {step_desc} ✓")
            else:
                st.markdown(
                    f"<div style='padding:1rem; border:1px solid #ddd; border-radius:0.5rem; color:#888;'>"
                    f"<b>{step_label}</b>: {step_desc}</div>", 
                    unsafe_allow_html=True
                )
    st.markdown("<br>", unsafe_allow_html=True)

def render_step1():
    st.markdown("### Job Description Input")
    st.markdown("Provide the job requirements. The internal LLM engine will dynamically extract all entities, skills, and explainability parameters.")
    
    input_method = st.radio("Choose Input Method", ["Paste Job Description", "Upload Job Description Document"], horizontal=True)
    jd_content = ""
    
    if input_method == "Paste Job Description":
        jd_content = st.text_area(
            "Job Description Content", 
            height=300, 
            placeholder="Paste your complete job description here..."
        )
    else:
        uploaded_file = st.file_uploader("Upload JD Document", type=["pdf", "docx", "txt"])
        if uploaded_file is not None:
            if uploaded_file.name.endswith(".txt"):
                jd_content = uploaded_file.getvalue().decode("utf-8")
                st.success("Text file read successfully.")
            else:
                st.info("Simulating text extraction for document...")
                jd_content = f"Title: {uploaded_file.name.split('.')[0]}\nSample content extracted from document..."
    
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Analyze Job Description", type="primary", use_container_width=True):
            if not jd_content.strip():
                st.error("Please provide a Job Description to analyze.")
            else:
                run_ai_analysis(jd_content)
                st.rerun()
    with c2:
        if storage.load_personas():
            if st.button("Skip to Upload (Use Existing Persona)", use_container_width=True):
                set_step(3)
                st.rerun()

def render_step2():
    st.markdown("### AI Hiring Blueprint Validation")
    st.success("AI successfully extracted the hiring blueprint with confidence scores. Hover over the `?` icons to see the AI's source extraction logic.")
    
    raw = st.session_state.raw_blueprint
    flat = st.session_state.flat_blueprint
    
    comp_raw = raw.get("company_information", {})
    pos_raw = raw.get("position_details", {})
    exp_raw = raw.get("experience", {})
    edu_raw = raw.get("education", {})
    tech_raw = raw.get("technology_stack", {})
    
    tabs = st.tabs([
        "1. Position & Company", 
        "2. Role & Responsibilities", 
        "3. Skills & Tech Stack", 
        "4. Business & Risks", 
        "5. Scoring Engine", 
        "6. Interview Kit"
    ])
    
    # --- Tab 1: Position & Company ---
    with tabs[0]:
        st.markdown("#### Position Details")
        c1, c2, c3 = st.columns(3)
        flat["job_title"] = c1.text_input("Job Title", u_val(pos_raw.get("job_title")), help=u_help(pos_raw.get("job_title")))
        flat["department"] = c2.text_input("Department", u_val(pos_raw.get("department")), help=u_help(pos_raw.get("department")))
        flat["job_level"] = c3.text_input("Job Level", u_val(pos_raw.get("job_level")), help=u_help(pos_raw.get("job_level")))
        
        c4, c5, c6 = st.columns(3)
        flat["employment_type"] = c4.text_input("Employment Type", u_val(pos_raw.get("employment_type")), help=u_help(pos_raw.get("employment_type")))
        flat["work_mode"] = c5.text_input("Work Mode", u_val(pos_raw.get("work_mode")), help=u_help(pos_raw.get("work_mode")))
        flat["location"] = c6.text_input("Location", u_val(pos_raw.get("location")), help=u_help(pos_raw.get("location")))
        
        st.markdown("---")
        st.markdown("#### Company Information")
        cc1, cc2, cc3 = st.columns(3)
        flat["company_name"] = cc1.text_input("Company Name", u_val(comp_raw.get("company_name")), help=u_help(comp_raw.get("company_name")))
        flat["industry"] = cc2.text_input("Industry", u_val(comp_raw.get("industry")), help=u_help(comp_raw.get("industry")))
        flat["company_size"] = cc3.text_input("Company Size", u_val(comp_raw.get("company_size")), help=u_help(comp_raw.get("company_size")))

    # --- Tab 2: Role & Responsibilities ---
    with tabs[1]:
        st.markdown("#### Role Summary")
        flat["job_summary"] = st.text_area("Job Summary", u_val(raw.get("job_summary")), height=100, help=u_help(raw.get("job_summary")))
        
        st.markdown("#### Experience & Education")
        e1, e2 = st.columns(2)
        flat["experience_min"] = e1.text_input("Minimum Years", u_val(exp_raw.get("minimum_years")), help=u_help(exp_raw.get("minimum_years")))
        flat["education_req"] = e2.text_input("Education Requirement", u_val(edu_raw.get("degree_required")), help=u_help(edu_raw.get("degree_required")))
        
        st.markdown("#### Responsibilities")
        resp_list = u_list(raw.get("responsibilities"), "value")
        edited_resp = st.text_area("Responsibilities (One per line)", "\n".join(resp_list), height=200)
        flat["responsibilities"] = [r.strip() for r in edited_resp.split("\n") if r.strip()]

    # --- Tab 3: Skills & Tech Stack ---
    with tabs[2]:
        st.markdown("#### Core Skills")
        
        c1, c2 = st.columns(2)
        with c1:
            m_skills = u_list(raw.get("mandatory_skills"), "name")
            flat["mandatory_skills"] = st.multiselect("Mandatory Skills", options=m_skills, default=m_skills, help="AI Extracted Mandatory Skills")
        with c2:
            p_skills = u_list(raw.get("preferred_skills"), "name")
            flat["preferred_skills"] = st.multiselect("Preferred Skills", options=p_skills, default=p_skills, help="AI Extracted Preferred Skills")

        st.markdown("---")
        st.markdown("#### Technology Stack")
        t1, t2, t3 = st.columns(3)
        
        def render_tech(col, label, key):
            items = u_list(tech_raw.get(key), "name")
            return col.multiselect(label, options=items, default=items)
            
        flat["tech_programming"] = render_tech(t1, "Programming", "programming")
        flat["tech_cloud"] = render_tech(t2, "Cloud Platforms", "cloud_platforms")
        flat["tech_databases"] = render_tech(t3, "Databases", "databases")
        
        t4, t5, _ = st.columns(3)
        flat["tech_frameworks"] = render_tech(t4, "Frameworks", "frameworks")
        flat["tech_tools"] = render_tech(t5, "Tools & DevOps", "tools")

    # --- Tab 4: Business & Risks ---
    with tabs[3]:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Soft Skills")
            soft_skills = u_list(raw.get("soft_skills"), "name")
            edited_soft = st.text_area("Soft Skills (One per line)", "\n".join(soft_skills), height=150)
            flat["soft_skills"] = [s.strip() for s in edited_soft.split("\n") if s.strip()]
            
        with c2:
            st.markdown("#### Identified Hiring Risks")
            risks = u_list(raw.get("hiring_risks"), "value")
            if risks:
                for r in risks:
                    st.warning(r)
            else:
                st.info("No significant risks identified by AI.")

    # --- Tab 5: Scoring Engine ---
    with tabs[4]:
        st.markdown("#### Resume Evaluation Weights")
        weights = raw.get("score_weights") or {}
        
        sw1, sw2 = st.columns(2)
        with sw1:
            w_mand = st.slider("Mandatory Skills", 0, 100, int(weights.get("mandatory_skills", 40)))
            w_exp = st.slider("Experience Match", 0, 100, int(weights.get("experience", 20)))
            w_dom = st.slider("Domain Knowledge", 0, 100, int(weights.get("domain_knowledge", 10)))
        with sw2:
            w_pref = st.slider("Preferred Skills", 0, 100, int(weights.get("preferred_skills", 15)))
            w_edu = st.slider("Education", 0, 100, int(weights.get("education", 5)))
            w_sem = st.slider("Semantic Match", 0, 100, int(weights.get("semantic_match", 10)))
            
        total_weight = w_mand + w_exp + w_dom + w_pref + w_edu + w_sem
        flat["score_weights"] = {
            "mandatory_skills": w_mand, "experience": w_exp, "domain_knowledge": w_dom, 
            "preferred_skills": w_pref, "education": w_edu, "semantic_match": w_sem
        }
        
        if total_weight == 100:
            st.success("Weights perfectly balanced (100%).")
        else:
            st.error(f"Weights total {total_weight}%. Adjust sliders to exactly 100%.")

    # --- Tab 6: Interview Kit ---
    with tabs[5]:
        st.markdown("#### AI Generated Interview Questions")
        questions = raw.get("interview_questions") or {}
        
        for q_type, q_list in questions.items():
            parsed_qs = u_list(q_list, "value")
            if parsed_qs:
                with st.expander(f"📌 {q_type.replace('_', ' ').title()} Questions"):
                    for q in parsed_qs:
                        st.markdown(f"- {q}")
        flat["interview_questions"] = {k: u_list(v, "value") for k, v in questions.items()}

def render_step3():
    st.markdown("### Select Persona & Upload Resumes")
    
    saved_personas = storage.load_personas()

    if not saved_personas:
        st.warning("No Hiring Personas saved yet. Please go back to Step 1 to create one.")
        if st.button("← Back to Step 1"):
            set_step(1)
            st.rerun()
        return

    st.markdown("#### 1. Select Hiring Persona")
    
    persona_options = {}
    for p in saved_personas: 
        display_name = f"{p.get('job_title', 'Role')} ({p.get('location', 'Loc')}) - {p['created_at']}"
        persona_options[display_name] = p['id']
        
    default_index = 0
    if st.session_state.selected_persona_id:
        for i, p_id in enumerate(persona_options.values()):
            if p_id == st.session_state.selected_persona_id:
                default_index = i
                break

    selected_display = st.selectbox(
        "Choose an active blueprint to match against:", 
        options=list(persona_options.keys()), 
        index=default_index
    )
    
    st.session_state.selected_persona_id = persona_options[selected_display]
    active_p = storage.load_persona(
        st.session_state.selected_persona_id
    )
    
    with st.expander(f"📌 Active Profile Summary: {active_p.get('job_title', 'Untitled')}", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Required Experience", active_p.get("experience_min", "N/A"))
        c2.metric("Location", active_p.get("location", "N/A"))
        c3.metric("Mandatory Skills", len(active_p.get("mandatory_skills", [])))
        c4.metric("Dept/BU", active_p.get("department", "N/A"))
        
        st.caption(f"**Core Stack:** {', '.join(active_p.get('mandatory_skills', [])[:7])}")

    st.markdown("---")
    
    st.markdown("#### 2. Upload Candidate Resumes")
    uploaded_files = st.file_uploader("Upload Resumes (PDF formats preferred)", type=["pdf", "docx"], accept_multiple_files=True)
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} resumes staged for screening against the **{active_p.get('job_title', 'Role')}** persona.")
        file_data = [{"File Name": f.name, "Size (KB)": round(f.size / 1024, 2)} for f in uploaded_files]
        st.dataframe(pd.DataFrame(file_data), use_container_width=True, hide_index=True)

def render_bottom_actions():
    st.markdown("---")
    c1, c2, c3 = st.columns([1, 1, 2])
    
    with c1:
        if st.session_state.step > 1:
            if st.button("← Start Over / New JD", use_container_width=True):
                set_step(1)
                st.rerun()
                
    with c2:
        if st.session_state.step == 2:
            if st.button("💾 Save Flattened Persona", type="secondary", use_container_width=True):
                save_current_persona()
                st.rerun()
                
    with c3:
        if st.session_state.step == 3:
            if st.button("🚀 Start AI Resume Matching", type="primary", use_container_width=True):
                active_p = storage.load_persona(
                    st.session_state.selected_persona_id
                )
                title = active_p.get("job_title", "Role")
                st.success(f"Starting vector matching engine for {title}! Navigating to results...")
                st.balloons()
        else:
            st.button("Start AI Resume Matching", type="primary", use_container_width=True, disabled=True)

# ==========================================
# MAIN APP LOOP
# ==========================================
def main():
    render_header()
    
    with st.container():
        if st.session_state.step == 1:
            render_step1()
        elif st.session_state.step == 2:
            render_step2()
        elif st.session_state.step == 3:
            render_step3()
            
    render_bottom_actions()

if __name__ == "__main__":
    main()

