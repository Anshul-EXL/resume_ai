import pypdf
import docx

def extract_text(file):
    if file.name.endswith('.pdf'):
        reader = pypdf.PdfReader(file)
        return "\n".join([page.extract_text() for page in reader.pages])
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        return "\n".join([para.text for para in doc.paragraphs])
    return ""

def parse_resume(file):
    text = extract_text(file)
    # Ideally, send to Ollama here to get JSON structure
    # For now, return a raw dict that the matcher can handle
    return {"text": text, "filename": file.name}