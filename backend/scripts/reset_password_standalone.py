"""
Standalone script to reset password for test user.
Uses bcrypt directly without app dependencies.
"""
import os
import sys
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Reset password for test user
    email = "john.doe.11@student.hillsboro.edu"
    new_password = "Student123!"

    print(f"Resetting password for {email}...")

    # Hash password using bcrypt (same way as the app)
    salt = bcrypt.gensalt(rounds=12)
    password_hash = bcrypt.hashpw(new_password.encode("utf-8"), salt).decode("utf-8")

    result = session.execute(
        text("UPDATE users SET password_hash = :password_hash WHERE email = :email"),
        {"password_hash": password_hash, "email": email},
    )

    session.commit()

    if result.rowcount > 0:
        print(f"✓ Password reset successfully for {email}")
        print(f"  New password: {new_password}")
    else:
        print(f"✗ User not found: {email}")

except Exception as e:
    print(f"✗ Error: {e}")
    session.rollback()
finally:
    session.close()
