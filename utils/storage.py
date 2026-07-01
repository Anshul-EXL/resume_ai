import json
import uuid
from pathlib import Path
from datetime import datetime

# ==========================================================
# STORAGE PATHS
# ==========================================================
BASE_DIR = Path("data")

PERSONA_DIR = BASE_DIR / "personas"
RESUME_DIR = BASE_DIR / "resumes"
MATCH_DIR = BASE_DIR / "matches"

PERSONA_DIR.mkdir(parents=True, exist_ok=True)
RESUME_DIR.mkdir(parents=True, exist_ok=True)
MATCH_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================
# COMMON
# ==========================================================
def _write_json(path: Path, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _read_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ==========================================================
# PERSONA
# ==========================================================
def save_persona(persona: dict):
    """
    Save Hiring Persona
    """

    if "id" not in persona:
        persona["id"] = str(uuid.uuid4())

    persona["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file_path = PERSONA_DIR / f"{persona['id']}.json"

    _write_json(file_path, persona)

    return persona["id"]


def load_personas():
    personas = []

    for file in PERSONA_DIR.glob("*.json"):
        personas.append(_read_json(file))

    personas.sort(
        key=lambda x: x.get("created_at", ""),
        reverse=True
    )

    return personas


def load_persona(persona_id):
    file_path = PERSONA_DIR / f"{persona_id}.json"

    if not file_path.exists():
        return None

    return _read_json(file_path)


def delete_persona(persona_id):
    file_path = PERSONA_DIR / f"{persona_id}.json"

    if file_path.exists():
        file_path.unlink()


# ==========================================================
# RESUME
# ==========================================================
def save_resume(candidate: dict):
    """
    candidate should already contain extracted information
    """

    if "id" not in candidate:
        candidate["id"] = str(uuid.uuid4())

    candidate["uploaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    file_path = RESUME_DIR / f"{candidate['id']}.json"

    _write_json(file_path, candidate)

    return candidate["id"]


def load_resume(resume_id):
    file_path = RESUME_DIR / f"{resume_id}.json"

    if not file_path.exists():
        return None

    return _read_json(file_path)


def load_resumes():
    resumes = []

    for file in RESUME_DIR.glob("*.json"):
        resumes.append(_read_json(file))

    resumes.sort(
        key=lambda x: x.get("uploaded_at", ""),
        reverse=True
    )

    return resumes


def delete_resume(resume_id):
    file_path = RESUME_DIR / f"{resume_id}.json"

    if file_path.exists():
        file_path.unlink()


# ==========================================================
# MATCH RESULTS
# ==========================================================
def save_match(job_id, results):
    file_path = MATCH_DIR / f"{job_id}.json"

    _write_json(file_path, results)


def load_match(job_id):
    file_path = MATCH_DIR / f"{job_id}.json"

    if not file_path.exists():
        return None

    return _read_json(file_path)


# ==========================================================
# DASHBOARD
# ==========================================================
def get_dashboard_stats():

    return {
        "personas": len(list(PERSONA_DIR.glob("*.json"))),
        "resumes": len(list(RESUME_DIR.glob("*.json"))),
        "matches": len(list(MATCH_DIR.glob("*.json")))
    }