#!/usr/bin/env python3
"""Quick script to check users in database"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal
from app.models import User
from app.auth.security import verify_password

db = SessionLocal()
users = db.query(User).all()

print(f"Total users: {len(users)}")
print("-" * 50)

for user in users:
    print(f"ID: {user.id}")
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Role: {user.role}")
    print(f"Password hash: {user.password_hash[:60]}...")
    print(f"Last login: {user.last_login_at}")

    # Test password verification with common test passwords
    test_passwords = ['password123', 'test123456', '123456', 'admin123']
    for pwd in test_passwords:
        try:
            if verify_password(pwd, user.password_hash):
                print(f"  ✓ Password '{pwd}' VERIFIED!")
        except Exception as e:
            print(f"  ✗ Password '{pwd}' failed: {e}")
    print("-" * 50)

db.close()
