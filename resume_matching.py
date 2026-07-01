import streamlit as st
import pandas as pd
from utils.storage import load_all_personas
from services.ollama_service import OllamaExtractionEngine

st.set_page_config(layout="wide", page_title="Resume Matching")
st.title("🚀 Resume Screening & Ranking")

# 1. Load available personas
personas = load_all_personas()
if not personas:
    st.warning("No personas found. Please create one in Hiring Manager first.")
    st.stop()

# 2. Select Persona
selected_p_name = st.selectbox("Select Hiring Persona", [p.get('title', 'Untitled') for p in personas])
active_p = next(p for p in personas if p.get('title') == selected_p_name)

# 3. Upload Resumes
uploaded_files = st.file_uploader("Upload Resumes", accept_multiple_files=True)

def calculate_score(resume_data, persona):
    """Weighted Scoring Algorithm"""
    score = 0
    weights = persona.get('weights', {})
    
    # Skills match
    resume_skills = set(resume_data.get('skills', []))
    persona_skills = set(persona.get('skills', []))
    match = len(resume_skills.intersection(persona_skills)) / len(persona_skills) if persona_skills else 0
    score += match * weights.get('mandatory_skills', 40)
    
    # Experience match
    res_exp = resume_data.get('years_of_experience', 0)
    req_exp = int(persona.get('exp', 0))
    exp_match = min(res_exp / req_exp, 1.0) if req_exp > 0 else 1.0
    score += exp_match * weights.get('experience', 20)
    
    return round(score, 2)

if uploaded_files and st.button("Run Matching Engine"):
    results = []
    with st.spinner("Analyzing resumes..."):
        for f in uploaded_files:
            # Simplified text extraction (In production, use a PDF library like pypdf)
            resume_text = f.read().decode('utf-8', errors='ignore')
            data = OllamaExtractionEngine.parse_resume(resume_text)
            
            # Score
            score = calculate_score(data, active_p)
            results.append({"Candidate": f.name, "Score": score, "Skills": ", ".join(data.get('skills', []))})
    
    # 4. Display Results
    df = pd.DataFrame(results).sort_values(by="Score", ascending=False)
    st.dataframe(df, use_container_width=True)
    
    st.success("Matching complete!")
