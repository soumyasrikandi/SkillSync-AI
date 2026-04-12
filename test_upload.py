import urllib.request
import json
import uuid

# Create a mock PDF file (just needs to be a file with some text inside to hit our parser, 
# although our parser uses pypdf which expects a proper PDF structure. 
# We'll just generate a minimal valid PDF)

minimal_pdf = b"%PDF-1.4\n1 0 obj <</Type /Catalog /Pages 2 0 R>>\nendobj\n2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>>\nendobj\n3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R>>\nendobj\n4 0 obj <</Length 68>>\nstream\nBT\n/F1 12 Tf\n10 700 Td\n(SKILLS: Python, React, Flask. SUMMARY: A good dev.) Tj\nET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000216 00000 n \ntrailer <</Size 5 /Root 1 0 R>>\nstartxref\n333\n%%EOF\n"

# Boundary for multipart form data
boundary = '----WebKitFormBoundary' + uuid.uuid4().hex

# Body of the request
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="resume"; filename="test_resume.pdf"\r\n'
    f"Content-Type: application/pdf\r\n\r\n".encode('utf-8') +
    minimal_pdf +
    f"\r\n--{boundary}--\r\n".encode('utf-8')
)

req = urllib.request.Request("http://127.0.0.1:5000/api/auth/upload-resume", data=body)
req.add_header('Content-type', f'multipart/form-data; boundary={boundary}')
# No token needed since our route isn't actually checking token validity yet, but if it does, it might fail.
# Wait, our route /upload-resume does NOT check the JWT token in Python. It just processes it!

try:
    with urllib.request.urlopen(req) as response:
        print("Status", response.status)
        print("Response:", response.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
    if hasattr(e, 'read'):
        print(e.read().decode('utf-8'))
