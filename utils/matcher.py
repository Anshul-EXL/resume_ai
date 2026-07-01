from . import embeddings, scorer, resume_parser, storage

def match(persona_id, resume_file):
    # 1. Load Persona
    persona = storage.get_persona(persona_id)
    
    # 2. Parse Resume
    parsed_resume = resume_parser.parse_resume(resume_file)
    
    # 3. Embeddings
    persona_emb = embeddings.get_embedding(str(persona['responsibilities']))
    resume_emb = embeddings.get_embedding(parsed_resume['text'])
    
    # 4. Score
    semantic_score = embeddings.compute_similarity(persona_emb, resume_emb)
    skill_score = scorer.calculate_skill_score(parsed_resume.get('skills', []), persona.get('mandatory_skills', []))
    
    final_score = (semantic_score * 0.4) + (skill_score * 0.6) # Weighted
    
    return {
        "score": final_score,
        "semantic_match": semantic_score,
        "skill_match": skill_score
    }