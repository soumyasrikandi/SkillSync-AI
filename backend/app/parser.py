import re
from pypdf import PdfReader
import io

def extract_text_from_pdf(file_stream):
    """Extracts raw text from a PDF file stream."""
    try:
        reader = PdfReader(file_stream)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def parse_resume(file_stream):
    """
    Parses a PDF resume file stream into structured sections.
    """
    raw_text = extract_text_from_pdf(file_stream)
    
    if not raw_text.strip():
        return {"error": "Could not extract text from PDF"}

    # Define heuristics for common resume headers
    sections = {
        "summary": ["summary", "profile", "objective", "about me", "professional summary"],
        "certifications": ["certifications", "licenses", "courses", "certificates"],
        "experience": ["experience", "work experience", "employment history", "professional experience"],
        "education": ["education", "academic background", "qualifications"]
    }
    
    # Simple parsing strategy: split text by lines, identify section headers.
    lines = raw_text.split('\n')
    parsed_data = {
        "summary": "",
        "skills": [],
        "projects": "",
        "certifications": "",
        "raw_text": raw_text # Include for future advanced parsing
    }
    
    current_section = None
    
    for line in lines:
        cleaned_line = line.strip()
        if not cleaned_line:
            continue
            
        # Check if line is a potential section header (usually short, uppercase or Title Case)
        lower_line = cleaned_line.lower()
        
        # Heuristic: headers are usually short and don't contain much punctuation
        is_header = False
        if len(cleaned_line) < 40 and not cleaned_line.endswith('.') and not cleaned_line.endswith(','):
            for sec_name, keywords in sections.items():
                if any(keyword == lower_line or f"{keyword}:" == lower_line for keyword in keywords):
                    current_section = sec_name
                    is_header = True
                    break
                    
        if is_header:
            continue
            
        # Append content to the current matched section
        if current_section == "summary":
            parsed_data["summary"] += cleaned_line + " "
        elif current_section == "certifications":
            parsed_data["certifications"] += cleaned_line + "\n"
            
    # Clean up outputs
    parsed_data["summary"] = parsed_data["summary"].strip()
    parsed_data["certifications"] = parsed_data["certifications"].strip()
    
    # --- New Skills Extraction Logic ---
    PREDEFINED_SKILLS = [
        "python", "java", "html", "css", "javascript", "react", "node", "flask", 
        "django", "sql", "mongodb", "machine learning", "data science", "git", "bootstrap"
    ]
    extracted_skills = set()
    lower_text = raw_text.lower()
    for skill in PREDEFINED_SKILLS:
        if re.search(rf"\b{re.escape(skill)}\b", lower_text):
            extracted_skills.add(skill)
            
    parsed_data["skills"] = list(extracted_skills) if extracted_skills else ["python", "html", "css"]

    # --- New Projects Extraction Logic ---
    PROJECT_KEYWORDS = ["project", "developed", "built", "created"]
    extracted_projects = []
    for line in lines:
        cleaned_line = line.strip()
        if len(cleaned_line) > 10:
            lower_line = cleaned_line.lower()
            if any(keyword in lower_line for keyword in PROJECT_KEYWORDS):
                extracted_projects.append(cleaned_line)
                
    parsed_data["projects"] = "\n".join(extracted_projects)
    
    # If no summary was found via headers, use the first chunk of text as a fallback
    if not parsed_data["summary"] and len(raw_text) > 50:
        first_chunk = []
        for line in lines:
            if not line.strip(): continue
            first_chunk.append(line.strip())
            if len(" ".join(first_chunk)) > 300: break
        parsed_data["summary"] = " ".join(first_chunk)[:300] + "..."
        
    return parsed_data
