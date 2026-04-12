from flask import Blueprint, request, jsonify
from app.parser import parse_resume
from app.skills_db import ROLE_SKILLS_DB
from app.recommendations_db import RECOMMENDATIONS_DB
from app.questions_db import QUESTIONS_DB
from werkzeug.utils import secure_filename
import io
from app.config import Config
import jwt
import datetime
import uuid
import bcrypt

auth_bp = Blueprint('auth', __name__)

# Simple in-memory user storage
users_db = {}


@auth_bp.route('/signup', methods=['POST'])
@auth_bp.route('/register', methods=['POST'])
def signup():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')
    name = data.get('name', '')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    if email in users_db:
        return jsonify({"error": "User with this email already exists"}), 409

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    user_id = str(uuid.uuid4())
    
    users_db[email] = {
        "id": user_id,
        "email": email,
        "name": name,
        "password": hashed_password,
        "auth_provider": "local",
        "college": "",
        "branch": "",
        "graduation_year": "",
        "skills": [],
        "certifications": []
    }

    token = jwt.encode({
        'user_id': user_id,
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, Config.SECRET_KEY, algorithm='HS256')

    return jsonify({"message": "User registered successfully", "token": token, "name": name}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    user = users_db.get(email)
    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    
    if user.get('auth_provider') != 'local':
        return jsonify({"error": f"Please use {user.get('auth_provider')} to login"}), 401

    if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        return jsonify({"error": "Invalid email or password"}), 401

    # Generate JWT
    token = jwt.encode({
        'user_id': user['id'],
        'email': user['email'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, Config.SECRET_KEY, algorithm='HS256')

    return jsonify({"message": "Login successful", "token": token, "name": user['name']}), 200

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    # Placeholder for real Google Auth verification
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    name = data.get('name', 'Google User')
    
    if not email:
        return jsonify({"error": "Email required from Google auth"}), 400

    user = users_db.get(email)
    if not user:
        user_id = str(uuid.uuid4())
        users_db[email] = {
            "id": user_id,
            "email": email,
            "name": name,
            "auth_provider": "google",
            "college": "",
            "branch": "",
            "graduation_year": "",
            "skills": [],
            "certifications": []
        }
    else:
        user_id = user['id']

    token = jwt.encode({
        'user_id': user_id,
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, Config.SECRET_KEY, algorithm='HS256')

    return jsonify({"message": "Google Login successful", "token": token}), 200



@auth_bp.route('/upload-resume', methods=['POST'])
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({"error": "No resume file provided"}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"error": "No resume file selected"}), 400
        
    if file and file.filename.lower().endswith('.pdf'):
        # Read file into memory stream for pypdf
        file_stream = io.BytesIO(file.read())
        parsed_data = parse_resume(file_stream)
        
        if "error" in parsed_data:
            return jsonify(parsed_data), 400
            
        return jsonify({
            "message": "Resume parsed successfully",
            "data": parsed_data
        }), 200
        
    return jsonify({"error": "Only PDF files are supported"}), 400

@auth_bp.route('/analyze-skills', methods=['POST'])
def analyze_skills():
    data = request.get_json(silent=True) or {}
    
    role = data.get('role', 'Web Developer')
    if not role:
        role = 'Web Developer'
        
    user_skills = data.get('user_skills', [])
    if not user_skills:
        user_skills = ["python", "html", "css"]

    if role not in ROLE_SKILLS_DB:
        role = 'Web Developer'
        
    required_skills = ROLE_SKILLS_DB[role]
    user_skills_lower = [s.lower().strip() for s in user_skills]
    
    matched_skills = []
    missing_skills = []
    
    for req_skill in required_skills:
        req_norm = req_skill.lower().strip()
        matched = False
        for user_sk in user_skills_lower:
            if req_norm in user_sk or user_sk in req_norm:
                matched_skills.append(req_skill)
                matched = True
                break
        if not matched:
            missing_skills.append(req_skill)
            
    match_percentage = int((len(matched_skills) / len(required_skills)) * 100) if required_skills else 0
    
    return jsonify({
        "match": match_percentage,
        "missing": missing_skills,
        "required": required_skills,
        "user_skills": user_skills_lower
    }), 200

@auth_bp.route('/predict-interview', methods=['POST'])
def predict_interview():
    data = request.get_json(silent=True) or {}
    if not data or 'parsed_data' not in data or 'role' not in data:
        return jsonify({"error": "Missing parsed_data or role"}), 400
        
    parsed = data['parsed_data']
    role = data['role']
    
    # 1. Skills Match Score (0 - 100)
    user_skills = parsed.get("skills", [])
    required_skills = ROLE_SKILLS_DB.get(role, [])
    
    matched_skills = []
    user_skills_lower = [s.lower().strip() for s in user_skills]
    
    for req_skill in required_skills:
        req_norm = req_skill.lower().strip()
        for user_sk in user_skills_lower:
            if req_norm in user_sk or user_sk in req_norm:
                matched_skills.append(req_skill)
                break
                
    skills_score = int((len(matched_skills) / len(required_skills)) * 100) if required_skills else 0
    
    # 2. Projects Score (0 - 100)
    projects_text = parsed.get("projects", "")
    # Simple heuristic: 1 point per 2 characters of project description, max 100
    projects_score = min(int(len(projects_text.strip()) / 2), 100) if projects_text else 0
    
    # 3. Certifications Score (0 - 100)
    certs_text = parsed.get("certifications", "")
    certs_score = min(int(len(certs_text.strip()) / 1.5), 100) if certs_text else 0
    
    # 4. Communication Keywords Score (0 - 100)
    raw_text = parsed.get("raw_text", "").lower()
    comm_keywords = ["team", "lead", "collaborat", "manag", "present", "agile", "communicat"]
    keyword_matches = sum(1 for kw in comm_keywords if kw in raw_text)
    # Max score if 3 or more keywords are found
    comm_score = min(int((keyword_matches / 3) * 100), 100)
    
    # 5. Assessment Score (Optional Integration)
    assessment_score = data.get('assessment_score')
    
    if assessment_score is not None:
        # Overriding weighting parameters.
        # User requested: (Skill Gap * 0.4) + (Assessment * 0.3) + (Other factors * 0.3)
        # Skills 40%, Assessment 30%, Projects 15%, Comm 10%, Certs 5%
        overall_score = int(
            (skills_score * 0.40) + 
            (assessment_score * 0.30) +
            (projects_score * 0.15) + 
            (comm_score * 0.10) + 
            (certs_score * 0.05)
        )
    else:
        # Overall Score (Weighted Average)
        # Weights: Skills 40%, Projects 30%, Certifications 10%, Communication 20%
        overall_score = int((skills_score * 0.4) + (projects_score * 0.3) + (certs_score * 0.1) + (comm_score * 0.2))
    
    # Risk Level
    if overall_score < 50:
        risk_level = "High"
    elif overall_score < 75:
        risk_level = "Medium"
    else:
        risk_level = "Low"
        
    return jsonify({
        "success_percentage": overall_score,
        "risk_label": risk_level,
        "factors": {
            "Skills Match": skills_score,
            "Projects": projects_score,
            "Certifications": certs_score,
            "Communication": comm_score
        }
    }), 200

@auth_bp.route('/recommendations', methods=['POST'])
def get_recommendations():
    data = request.get_json(silent=True) or {}
    if not data or 'role' not in data or 'parsed_data' not in data:
        return jsonify({"error": "Missing role or parsed_data"}), 400
        
    role = data['role']
    parsed_data = data['parsed_data']
    
    user_skills_lower = [s.lower().strip() for s in parsed_data.get("skills", [])]
    required_skills = ROLE_SKILLS_DB.get(role, [])
    
    missing_skills = []
    
    for req_skill in required_skills:
        req_norm = req_skill.lower().strip()
        matched = False
        for user_sk in user_skills_lower:
            if req_norm in user_sk or user_sk in req_norm:
                matched = True
                break
        if not matched:
            missing_skills.append(req_skill)
            
    # Now map missing skills to recommendations
    recommendations = {
        "courses": [],
        "certifications": [],
        "learning_paths": []
    }
    
    seen_titles = set()
    
    def add_resource(res):
        if res["title"] in seen_titles: return
        seen_titles.add(res["title"])
        t = res["type"].lower()
        if t == "course": recommendations["courses"].append(res)
        elif t == "certification": recommendations["certifications"].append(res)
        elif t == "learning path": recommendations["learning_paths"].append(res)
    
    db_keys = list(RECOMMENDATIONS_DB.keys())
    
    if len(missing_skills) == 0:
        # Give some general defaults if none missing
        for res in RECOMMENDATIONS_DB["default"]: add_resource(res)
    else:
        for skill in missing_skills:
            skill_lower = skill.lower()
            mapped = False
            for db_key in db_keys:
                if db_key in skill_lower or skill_lower in db_key:
                    for res in RECOMMENDATIONS_DB[db_key]: add_resource(res)
                    mapped = True
            
            if not mapped:
                # Add default ones
                for res in RECOMMENDATIONS_DB["default"]: add_resource(res)
                
    return jsonify({
        "missing_skills": missing_skills,
        "recommendations": recommendations
    }), 200

import random

@auth_bp.route('/generate-assessment', methods=['POST'])
def generate_assessment():
    data = request.get_json(silent=True) or {}
    user_skills = data.get('skills', [])
    
    if not user_skills:
        # Fallback if no skills
        return jsonify({"questions": QUESTIONS_DB.get("default", [])}), 200
        
    user_skills_lower = [s.lower().strip() for s in user_skills]
    
    # Map skills to question categories
    matched_questions = []
    
    categories = list(QUESTIONS_DB.keys())
    for skill in user_skills_lower:
        for cat in categories:
            if cat in ["default", "general aptitude"]: continue
            # e.g., if 'html' in 'html/css'
            if cat in skill or skill in cat or any(part in skill for part in cat.split('/')):
                matched_questions.extend(QUESTIONS_DB[cat])
                
    # Also handle some generic mappings explicitly
    if any(s in ['html', 'css', 'javascript', 'react', 'frontend'] for s in user_skills_lower):
        matched_questions.extend(QUESTIONS_DB.get('html/css', []))
        matched_questions.extend(QUESTIONS_DB.get('javascript', []))
    if any(s in ['python', 'django', 'flask'] for s in user_skills_lower):
        matched_questions.extend(QUESTIONS_DB.get('python', []))
    if any(s in ['sql', 'database', 'mysql', 'postgresql'] for s in user_skills_lower):
        matched_questions.extend(QUESTIONS_DB.get('sql', []))
        
    # Deduplicate questions
    unique_questions = []
    seen_qs = set()
    for q in matched_questions:
        if q["q"] not in seen_qs:
            seen_qs.add(q["q"])
            unique_questions.append(q)
            
    # Return full pool to allow frontend to adaptively traverse.
    
    # We still ensure aptitude questions are attached
    aptitude_pool = QUESTIONS_DB.get("general aptitude", [])
    
    final_questions = unique_questions + aptitude_pool
    
    # Fallback to default if somehow we got 0 questions
    if len(final_questions) == 0:
        final_questions = QUESTIONS_DB.get("default", [])

    return jsonify({"questions": final_questions}), 200

@auth_bp.route('/get-profile', methods=['POST'])
def get_profile():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
        
    user = users_db.get(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    # Exclude sensitive info
    profile_data = {
        "email": user.get("email"),
        "name": user.get("name"),
        "college": user.get("college", ""),
        "branch": user.get("branch", ""),
        "graduation_year": user.get("graduation_year", ""),
        "skills": user.get("skills", []),
        "certifications": user.get("certifications", [])
    }
    return jsonify(profile_data), 200

@auth_bp.route('/update-profile', methods=['POST'])
def update_profile():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    
    if not email:
        return jsonify({"error": "Email is required"}), 400
        
    user = users_db.get(email)
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    allowed_fields = ["name", "college", "branch", "graduation_year", "skills", "certifications"]
    for field in allowed_fields:
        if field in data:
            user[field] = data[field]
            
    return jsonify({"message": "Profile updated successfully"}), 200

@auth_bp.route('/score-assessment', methods=['POST'])
def score_assessment():
    data = request.get_json(silent=True) or {}
    
    correct = data.get('correct_answers', 0)
    total = data.get('total_questions', 5)
    category_data = data.get('category_data', {})
    
    if total <= 0:
        return jsonify({"error": "Invalid total questions"}), 400
        
    percentage = (correct / total) * 100
    
    if percentage >= 75:
        readiness = "High readiness"
    elif percentage >= 50:
        readiness = "Medium readiness"
    else:
        readiness = "Low readiness"
        
    # Process category specific scores
    category_scores = {}
    for cat, stats in category_data.items():
        cat_total = stats.get('total', 0)
        cat_correct = stats.get('correct', 0)
        if cat_total > 0:
            category_scores[cat] = int((cat_correct / cat_total) * 100)
        
    return jsonify({
        "score": round(percentage),
        "readiness": readiness,
        "category_scores": category_scores
    }), 200

