import requests
import time

BASE_URL = "http://127.0.0.1:5000/api/auth"

print("1. Registering user...")
res = requests.post(f"{BASE_URL}/register", json={
    "name": "Jane Doe",
    "email": "jane_otp@test.com",
    "password": "password"
})
print("Register Status:", res.status_code)
print("Register Response:", res.json())

print("\n2. Trying to login WITHOUT verifying...")
res = requests.post(f"{BASE_URL}/login", json={
    "email": "jane_otp@test.com",
    "password": "password"
})
print("Login Status:", res.status_code)
print("Login Response:", res.json())
