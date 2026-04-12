import bcrypt
import uuid
import random
from datetime import datetime, timedelta

# In-memory storage for users
# Structure: { "email@example.com": { "id": "...", "email": "...", "password": "...", "name": "...", "auth_provider": "local", "is_verified": bool, "otp": str, "otp_expires": datetime } }
users_db = {}

class User:
    @staticmethod
    def create_user(email, password, name=""):
        if email in users_db:
            return None
        
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user_id = str(uuid.uuid4())
        
        users_db[email] = {
            "id": user_id,
            "email": email,
            "password": hashed_password.decode('utf-8'),
            "name": name,
            "auth_provider": "local",
            "is_verified": True,
            "otp": None,
            "otp_expires": None,
            "college": "",
            "branch": "",
            "graduation_year": "",
            "skills": [],
            "certifications": []
        }
        return user_id

    @staticmethod
    def create_google_user(email, name=""):
        if email in users_db:
            return None
            
        user_id = str(uuid.uuid4())
        users_db[email] = {
            "id": user_id,
            "email": email,
            "name": name,
            "auth_provider": "google",
            "is_verified": True, # Google auth is pre-verified
            "otp": None,
            "otp_expires": None,
            "college": "",
            "branch": "",
            "graduation_year": "",
            "skills": [],
            "certifications": []
        }
        return user_id

    @staticmethod
    def find_by_email(email):
        return users_db.get(email)

    @staticmethod
    def verify_password(stored_password, provided_password):
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))



    @staticmethod
    def update_profile(email, data):
        user = users_db.get(email)
        if not user:
            return None
            
        allowed_fields = ["name", "college", "branch", "graduation_year", "skills", "certifications"]
        for field in allowed_fields:
            if field in data:
                user[field] = data[field]
                
        return user
