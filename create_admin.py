#!/usr/bin/env python3
"""
Admin Setup Script
Creates the first admin user for the leadership development platform.
Run this script to create your admin account.
"""

import sys
import os
from datetime import datetime

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def create_admin_user():
    """Create the first admin user"""
    
    print("🔐 Admin Account Setup")
    print("=" * 50)
    
    # Get admin details from user
    email = input("Enter your admin email: ").strip()
    if not email:
        print("❌ Email is required!")
        return
    
    username = input("Enter your username: ").strip()
    if not username:
        print("❌ Username is required!")
        return
    
    full_name = input("Enter your full name: ").strip()
    if not full_name:
        print("❌ Full name is required!")
        return
    
    mobile_number = input("Enter your mobile number: ").strip()
    if not mobile_number:
        print("❌ Mobile number is required!")
        return
    
    password = input("Enter your password (min 8 characters): ").strip()
    if len(password) < 8:
        print("❌ Password must be at least 8 characters!")
        return
    
    # Confirm password
    confirm_password = input("Confirm your password: ").strip()
    if password != confirm_password:
        print("❌ Passwords don't match!")
        return
    
    # Connect to database
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username) | (User.mobile_number == mobile_number)
        ).first()
        
        if existing_user:
            print(f"❌ User already exists with email: {existing_user.email}")
            return
        
        # Create admin user
        admin_user = User(
            email=email,
            username=username,
            full_name=full_name,
            mobile_number=mobile_number,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
            is_email_verified=True,  # Skip email verification for admin
            terms_accepted=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("\n✅ Admin account created successfully!")
        print("=" * 50)
        print(f"📧 Email: {admin_user.email}")
        print(f"👤 Username: {admin_user.username}")
        print(f"👨‍💼 Full Name: {admin_user.full_name}")
        print(f"🔑 Role: {admin_user.role.value}")
        print(f"📱 Mobile: {admin_user.mobile_number}")
        print(f"✅ Email Verified: {admin_user.is_email_verified}")
        print(f"🆔 User ID: {admin_user.id}")
        print("=" * 50)
        print("\n🚀 You can now login to the admin panel!")
        print("📝 Login URL: http://localhost:8001/api/v1/auth/login")
        print("🔧 Admin Panel: http://localhost:8001/api/v1/admin/dashboard")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

def list_existing_admins():
    """List existing admin users"""
    db = SessionLocal()
    
    try:
        admins = db.query(User).filter(User.role == UserRole.ADMIN).all()
        
        if not admins:
            print("📝 No admin users found.")
            return
        
        print("\n👨‍💼 Existing Admin Users:")
        print("=" * 50)
        for admin in admins:
            print(f"📧 Email: {admin.email}")
            print(f"👤 Username: {admin.username}")
            print(f"👨‍💼 Name: {admin.full_name}")
            print(f"🆔 ID: {admin.id}")
            print(f"✅ Active: {admin.is_active}")
            print(f"📅 Created: {admin.created_at}")
            print("-" * 30)
            
    except Exception as e:
        print(f"❌ Error listing admins: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🎯 Leadership Development Platform - Admin Setup")
    print("=" * 60)
    
    while True:
        print("\nChoose an option:")
        print("1. Create new admin user")
        print("2. List existing admins")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            create_admin_user()
        elif choice == "2":
            list_existing_admins()
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")
