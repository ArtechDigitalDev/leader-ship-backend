# Render Deployment Guide for Leadership Development Platform

## 🚀 Render Deployment Configuration

### **1. Environment Variables Setup**

In your Render dashboard, go to your service settings and add these environment variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://leadership_backend_db_user:xcmAqIu1Zlwfn3askqdJgXbucjh2jPJb@dpg-d31634t6ubrc73c4h940-a.oregon-postgres.render.com/leadership_backend_db

# Security Configuration (CHANGE THESE!)
SECRET_KEY=your-super-secret-production-key-change-this-immediately
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
DEBUG=False
ENVIRONMENT=production
API_V1_STR=/api/v1
PROJECT_NAME=Leadership Development Platform

# CORS Configuration (Add your frontend domain)
BACKEND_CORS_ORIGINS=["https://your-frontend-domain.com", "https://your-app.onrender.com"]

# Render Configuration
PORT=8000
WORKERS=1
```

### **2. Build Command**
```bash
pip install -r requirements.txt
```

### **3. Start Command**
```bash
python start.py
```

### **4. Database Migration**

After deployment, you need to run database migrations. You can do this by:

1. **Option A: SSH into Render service** (if available)
   ```bash
   alembic upgrade head
   ```

2. **Option B: Add migration to build command**
   ```bash
   pip install -r requirements.txt && alembic upgrade head
   ```

3. **Option C: Create admin user via API**
   ```bash
   # Use the create_admin.py script or API endpoints
   ```

### **5. Render Service Configuration**

- **Runtime**: Python 3.13
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python start.py`
- **Environment**: Python
- **Region**: Oregon (US West)

### **6. Database Connection Test**

Test your production database connection:

```python
# Test script
import os
os.environ['DATABASE_URL'] = 'postgresql://leadership_backend_db_user:xcmAqIu1Zlwfn3askqdJgXbucjh2jPJb@dpg-d31634t6ubrc73c4h940-a.oregon-postgres.render.com/leadership_backend_db'

from app.core.database import SessionLocal
from sqlalchemy import text

try:
    db = SessionLocal()
    result = db.execute(text('SELECT 1'))
    print("✅ Database connection successful!")
    db.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```

### **7. Production Checklist**

- [ ] Environment variables set in Render
- [ ] Database migrations run
- [ ] Admin user created
- [ ] CORS origins configured
- [ ] Secret key changed
- [ ] SSL certificate active
- [ ] Domain configured (if custom)

### **8. Monitoring**

- Check Render logs for any errors
- Monitor database connections
- Test API endpoints
- Verify admin panel access

### **9. API Endpoints**

Your production API will be available at:
- **Base URL**: `https://your-app-name.onrender.com`
- **API Docs**: `https://your-app-name.onrender.com/docs`
- **Admin Panel**: `https://your-app-name.onrender.com/api/v1/admin/dashboard`

### **10. Security Notes**

- Change the SECRET_KEY in production
- Use HTTPS only
- Configure proper CORS origins
- Monitor for suspicious activity
- Regular security updates

## 🔧 Troubleshooting

### Common Issues:

1. **Database Connection Failed**
   - Check DATABASE_URL format
   - Verify credentials
   - Ensure database is running

2. **Migration Errors**
   - Run `alembic current` to check status
   - Use `alembic upgrade head` to apply migrations

3. **CORS Issues**
   - Update BACKEND_CORS_ORIGINS
   - Check frontend domain

4. **Authentication Issues**
   - Verify SECRET_KEY is set
   - Check token expiration settings

## 📞 Support

If you encounter issues:
1. Check Render logs
2. Test database connection
3. Verify environment variables
4. Check API documentation at `/docs`
