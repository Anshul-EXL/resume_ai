import streamlit as st
import utils.storage as storage

st.set_page_config(layout="wide")
st.title("Hiring Personas")

if st.button("+ Create New Persona"):
    st.switch_page("pages/1_Hiring_Manager.py")

personas = storage.load_all_personas()
cols = st.columns(3)

for i, p in enumerate(personas):
    # Safely extract job title using .get() chains
    blueprint = p.get('approved_blueprint', {})
    
    # Handle the structure variation: 
    # Some objects might have job_title inside 'position_details' (as seen in services/ollama_service.py)
    # while others might have it at the top level of 'approved_blueprint'
    job_title = blueprint.get('job_title') or \
                blueprint.get('position_details', {}).get('job_title', {}).get('value') or \
                "Untitled Role"

    with cols[i % 3].container(border=True):
        st.subheader(job_title)
        st.caption(f"Status: {p.get('status', 'DRAFT')}")
        if st.button("Open", key=p['id']):
            st.session_state.selected_persona = p
            # Logic for opening would go here
            st.write(f"Selected: {job_title}")
