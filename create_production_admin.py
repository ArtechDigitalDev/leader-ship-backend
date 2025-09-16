#!/usr/bin/env python3
"""
Production Admin Creation Script
Creates admin user in the production Render database
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set production database URL
os.environ['DATABASE_URL'] = 'postgresql://leadership_backend_db_user:xcmAqIu1Zlwfn3askqdJgXbucjh2jPJb@dpg-d31634t6ubrc73c4h940-a.oregon-postgres.render.com/leadership_backend_db'

from app.core.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def create_production_admin():
    """Create admin user in production database"""
    
    print("🔐 Creating Production Admin User")
    print("=" * 50)
    
    db = SessionLocal()
    
    try:
        # Check if admin already exists
        existing_admin = db.query(User).filter(
            (User.email == 'sha237mim@gmail.com') | 
            (User.role == UserRole.ADMIN)
        ).first()
        
        if existing_admin:
            print(f"⚠️  Admin user already exists:")
            print(f"📧 Email: {existing_admin.email}")
            print(f"👤 Username: {existing_admin.username}")
            print(f"🔑 Role: {existing_admin.role.value}")
            return
        
        # Create production admin user
        admin_user = User(
            email='sha237mim@gmail.com',
            username='ShamimAdmin',
            full_name='Shamim Mahbub',
            mobile_number='01720506789',
            hashed_password=get_password_hash('jibon123lead'),
            role=UserRole.ADMIN,
            is_active=True,
            is_superuser=True,
            is_email_verified=True,
            terms_accepted=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("✅ Production admin user created successfully!")
        print("=" * 50)
        print(f"📧 Email: {admin_user.email}")
        print(f"👤 Username: {admin_user.username}")
        print(f"👨‍💼 Full Name: {admin_user.full_name}")
        print(f"🔑 Role: {admin_user.role.value}")
        print(f"📱 Mobile: {admin_user.mobile_number}")
        print(f"✅ Email Verified: {admin_user.is_email_verified}")
        print(f"🆔 User ID: {admin_user.id}")
        print("=" * 50)
        print("\n🚀 You can now login to the production system!")
        print("🌐 Production URL: https://your-app-name.onrender.com")
        print("📝 Login Endpoint: https://your-app-name.onrender.com/api/v1/auth/login")
        print("🔧 Admin Panel: https://your-app-name.onrender.com/api/v1/admin/dashboard")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_production_admin()
