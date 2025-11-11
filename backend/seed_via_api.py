#!/usr/bin/env python3
"""
Quick seed script that runs via HTTP endpoint
"""
import requests
import sys

API_URL = "https://dev-vividly-api-rm2v4spyrq-uc.a.run.app"

# Try to register a test student
response = requests.post(
    f"{API_URL}/api/v1/auth/register",
    json={
        "email": "john.doe.11@student.hillsboro.edu",
        "password": "Student123!",
        "first_name": "John",
        "last_name": "Doe",
        "role": "student"
    }
)

print(f"Register student: {response.status_code} - {response.text}")

# Try to login
response = requests.post(
    f"{API_URL}/api/v1/auth/login",
    json={
        "email": "john.doe.11@student.hillsboro.edu",
        "password": "Student123!"
    }
)

print(f"Login: {response.status_code} - {response.text}")

if response.status_code == 200:
    print("✓ Database seeding successful!")
    sys.exit(0)
else:
    print("✗ Failed to seed database")
    sys.exit(1)
