"""
Admin user initialization script.

Creates the default admin user if it doesn't exist.
Run this script after database initialization.
"""

import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from passlib.context import CryptContext
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models import User

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_admin_user():
    """Create the default admin user if it doesn't exist."""
    # Create database engine
    engine = create_engine(str(settings.database_url))
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if existing_admin:
            print("Admin user already exists.")
            print(f"  Username: {existing_admin.username}")
            print(f"  Email: {existing_admin.email}")
            print(f"  Role: {existing_admin.role}")
            return existing_admin

        # Create new admin user
        admin_user = User(
            username="admin",
            email="admin@innergarden.local",
            password_hash=pwd_context.hash("admin123456"),
            role="admin",
            status="active",
        )

        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)

        print("Admin user created successfully!")
        print(f"  Username: {admin_user.username}")
        print(f"  Email: {admin_user.email}")
        print(f"  Password: admin123456")
        print(f"  Role: {admin_user.role}")
        print("\nIMPORTANT: Please change the admin password after first login!")

        return admin_user

    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
        raise
    finally:
        db.close()


def reset_admin_password():
    """Reset the admin user password to default."""
    engine = create_engine(str(settings.database_url))
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            print("Admin user not found. Please run init_admin.py first.")
            return

        admin_user.password_hash = pwd_context.hash("admin123456")
        db.commit()

        print("Admin password has been reset to: admin123456")
        print("Please login and change the password immediately!")

    except Exception as e:
        db.rollback()
        print(f"Error resetting admin password: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Admin user management")
    parser.add_argument("--reset", action="store_true", help="Reset admin password to default")
    args = parser.parse_args()

    if args.reset:
        reset_admin_password()
    else:
        create_admin_user()
