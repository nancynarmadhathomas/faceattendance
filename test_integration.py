import requests
import base64
import os

# Create a dummy image
img_content = b'test_image_bytes'
img_b64 = base64.b64encode(img_content).decode()

# Use an existing employee test or create a new one
payload = {
    "employee_id": "test_app_user",
    "name": "App User Test",
    "email": "appuser@example.com",
    "department": "Engineering",
    "role": "employee",
    "password": "password123",
    "image": "data:image/jpeg;base64," + img_b64
}

try:
    print("Testing Registration API...")
    # NOTE: The generate_embedding will fail because it's not a real face,
    # but let's check the error handling or logic.
    res = requests.post("http://127.0.0.1:5000/api/register", json=payload)
    print("Response payload:", res.text)
except Exception as e:
    print("Request failed:", e)

