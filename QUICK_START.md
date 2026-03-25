# QUICK START GUIDE - Campaign OS Backend

Get the backend running in **5 minutes**.

## ⚡ Super Quick Start

```bash
cd /mnt/personal/election/campaign_backend

# 1. Install dependencies
uv sync

# 2. Setup database
mysql -u root -e "CREATE DATABASE campaign_os;"

# 3. Create .env
cp .env.example .env
# Edit .env with your DB credentials

# 4. Run migrations
python manage.py migrate

# 5. Create admin user
python manage.py createsuperuser

# 6. Load sample data
python manage.py seed_initial_data

# 7. Start server
python manage.py runserver 0.0.0.0:8000
```

## 🔗 Access Points

| URL | Purpose |
|-----|---------|
| http://localhost:8000/api/docs/ | API Documentation (Swagger) |
| http://localhost:8000/admin/ | Admin Panel |
| http://localhost:8000/api/schema/ | OpenAPI Schema |

## 📝 Login

**Default credentials after `createsuperuser`:**
- Username: Your chosen username
- Password: Your chosen password

## 🧪 Test API

Open browser console and run:

```javascript
const token = 'YOUR_ACCESS_TOKEN';
fetch('http://localhost:8000/api/v1/masters/districts/', {
  headers: { 'Authorization': `Bearer ${token}` }
})
.then(r => r.json())
.then(console.log);
```

## 📱 Next Steps

1. Login to `/api/docs/`
2. Create master data (Districts, Constituencies, Booths)
3. Add voter records
4. Assign volunteers
5. Create campaign events
6. View analytics dashboard

## 🆘 Troubleshooting

### Port Already in Use
```bash
python manage.py runserver 0.0.0.0:8001  # Use different port
```

### Database Connection Failed
```bash
# Check MySQL is running
sudo service mysql status

# Or update DB credentials in .env
```

### CORS Error
```bash
# Edit .env and add frontend origin
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://yourdomain.com
```

## 📚 Full Documentation

- **README.md** - Project overview
- **API_DOCUMENTATION.md** - Complete API reference
- **FRONTEND_INTEGRATION.md** - React integration guide

---

**That's it! You're ready to go. 🚀**
