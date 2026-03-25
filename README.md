# Campaign OS Backend

A production-ready Django REST Framework backend for managing election campaigns with complete geographic hierarchy, voter management, volunteer tracking, and real-time analytics.

## 📋 Features

### Core Features
- ✅ **Hierarchical Geographic Data**: Country → State → District → Constituency → Ward → Booth
- ✅ **Voter Management**: Registration, contact tracking, sentiment analysis
- ✅ **Volunteer Coordination**: Task assignment, attendance, performance metrics
- ✅ **Campaign Events**: Rally/meeting management with attendance tracking
- ✅ **Opinion Polls**: Survey creation and response collection
- ✅ **Grievance Management**: Issue tracking and resolution
- ✅ **Real-time Analytics**: Dashboard with aggregated campaign metrics

### Technical Features
- ✅ **JWT Authentication**: Secure token-based authentication
- ✅ **Role-Based Access Control**: 6 role types with hierarchical permissions
- ✅ **REST API**: Comprehensive RESTful API with filtering, search, pagination
- ✅ **Database**: Optimized MariaDB schema with strategic indexing
- ✅ **API Documentation**: Swagger UI and ReDoc auto-generated docs
- ✅ **Scalable Architecture**: Modular Django apps with clean separation of concerns

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React - /mnt/personal/election/election_mdk)    │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  Django REST API (This Backend)                            │
├─────────────────────────────────────────────────────────────┤
│ ┌────────────────┬───────────────┬──────────────────────┐  │
│ │  Accounts App  │  Masters App  │  Voters App          │  │
│ │  (Auth, RBAC)  │  (Geography)  │  (Voter data)        │  │
│ └────────────────┴───────────────┴──────────────────────┘  │
│ ┌────────────────┬───────────────┬──────────────────────┐  │
│ │ Volunteers App │  Campaigns    │ Elections & Polls     │  │
│ │                │  App          │                      │  │
│ └────────────────┴───────────────┴──────────────────────┘  │
│ ┌──────────────────────────────────────────────────────┐   │
│ │           Analytics App (Dashboards)                 │   │
│ └──────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  MariaDB Database (campaign_os)                            │
├─────────────────────────────────────────────────────────────┤
│  - 20+ Optimized Tables                                    │
│  - Strategic Indexes on Hot Paths                         │
│  - Foreign Key Relationships                              │
│  - Audit Trail (created_by, updated_by)                   │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Project Structure

```
campaign_backend/
├── campaign_os/              # Main Django project
│   ├── settings.py           # Django configuration
│   ├── urls.py               # Root URL routing
│   ├── wsgi.py               # Production WSGI server
│   │
│   ├── core/                 # Core utilities
│   │   ├── models.py         # BaseModel abstract class
│   │   └── middleware.py     # Custom middleware
│   │
│   ├── accounts/             # User & Authentication
│   │   ├── models.py         # User, Role, UserLog
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── masters/              # Geographic & Master Data
│   │   ├── models.py         # Country, State, District... Scheme, Issue
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── voters/               # Voter Management
│   │   ├── models.py         # Voter, VoterContact, VoterSurvey, Feedback
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── volunteers/           # Volunteer Management
│   │   ├── models.py         # Volunteer, VolunteerTask, Attendance
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── campaigns/            # Campaign Events
│   │   ├── models.py         # CampaignEvent, EventAttendee
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── elections/            # Elections & Polls
│   │   ├── models.py         # Election, Poll, PollQuestion, Response
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   └── analytics/            # Analytics & Dashboards
│       ├── models.py         # DashboardSnapshot
│       ├── views.py          # Analytics endpoints
│       └── urls.py
│
├── manage.py                 # Django CLI
├── pyproject.toml            # Dependencies (uv)
├── .env.example              # Environment template
├── setup.sh                  # Setup script
├── API_DOCUMENTATION.md      # Complete API docs
└── README.md                 # This file
```

## 🚀 Quick Start (5 Minutes)

### Prerequisites
- Python 3.10+
- MariaDB/MySQL 5.7+
- uv (Python package manager)

### Installation

```bash
# 1. Navigate to backend directory
cd /mnt/personal/election/campaign_backend

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Configure database in .env
nano .env  # Edit DB credentials

# 4. Run migrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Start development server
python manage.py runserver 0.0.0.0:8000
```

### Access the System

- **API Documentation**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/
- **Frontend**: http://localhost:5173/ (if running React app)

## 📡 API Examples

### 1. Login and Get Access Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

### 2. Get Voters by Booth

```bash
curl -X GET "http://localhost:8000/api/v1/voters/voters/?booth=1" \
  -H "Authorization: Bearer {access_token}"
```

### 3. Create New Voter Entry

```bash
curl -X POST http://localhost:8000/api/v1/voters/voters/ \
  -H "Authorization: Bearer {access_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ramesh Kumar",
    "voter_id": "A1234567",
    "phone": "9876543210",
    "booth": 1,
    "ward": 1,
    "address": "123 Main Street",
    "gender": "m",
    "sentiment": "positive"
  }'
```

### 4. Get Dashboard Statistics

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/dashboard/?constituency_id=100" \
  -H "Authorization: Bearer {access_token}"
```

### 5. List Booths with Coverage Stats

```bash
curl -X GET "http://localhost:8000/api/v1/analytics/booths/?constituency_id=100" \
  -H "Authorization: Bearer {access_token}"
```

## 🔐 Authentication

The system uses JWT (JSON Web Tokens) for authentication:

1. **Login**: POST `/api/v1/auth/login/` → Get access & refresh tokens
2. **Use Token**: Include `Authorization: Bearer {access_token}` in all requests
3. **Refresh**: Use refresh token to get new access token before expiration

### Token Expiration
- Access Token: 24 hours
- Refresh Token: 7 days

## 👥 Role-Based Access Control

| Role | Access Level | Use Case |
|------|--------------|----------|
| **Admin** | System-wide | Full control, all data |
| **District Head** | District + linked state | Oversee entire district |
| **Constituency Manager** | Constituency only | Manage specific constituency |
| **Volunteer** | Booth + ward | Field-level operations |
| **Analyst** | Read-only analytics | Data analysis, reporting |
| **Observer** | Limited read-only | Monitoring and compliance |

## 📊 Database Schema Highlights

### Key Tables

**Hierarchy:**
- `masters_country` → `masters_state` → `masters_district` → `masters_constituency` → `masters_ward` → `masters_booth`

**Voters:**
- `voters_voter` - Individual voter records
- `voters_votercontact` - Contact history
- `voters_votersurvey` - Survey responses
- `voters_voterfeedback` - Grievances/feedback
- `voters_voterpreference` - Communication preferences

**Volunteers:**
- `volunteers_volunteer` - Volunteer profiles
- `volunteers_volunteertask` - Task assignments
- `volunteers_volunteerattendance` - Daily attendance

**Campaigns:**
- `campaigns_campaignevent` - Events/rallies
- `campaigns_eventattendee` - Event attendance records

**Elections:**
- `elections_election` - Election metadata
- `elections_poll` - Opinion polls
- `elections_pollquestion` - Poll questions
- `elections_pollresponse` - Poll responses

## 🔍 Key APIs

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/auth/login/` | POST | User authentication |
| `/auth/users/me/` | GET | Current user info |
| `/auth/users/` | GET/POST | User management |
| `/masters/districts/` | GET | List districts |
| `/masters/booths/` | GET/POST | Booth CRUD |
| `/voters/voters/` | GET/POST | Voter management |
| `/voters/voters/uncontacted/` | GET | Uncontacted voters |
| `/voters/contacts/` | POST | Log voter contact |
| `/voters/feedbacks/` | GET/POST | Voter grievances |
| `/volunteers/volunteers/` | GET | Volunteer list |
| `/volunteers/tasks/` | POST | Assign tasks |
| `/campaigns/events/` | GET/POST | Campaign events |
| `/elections/polls/` | GET/POST | Opinion polls |
| `/analytics/dashboard/` | GET | Dashboard stats |
| `/analytics/booths/` | GET | Booth analytics |
| `/analytics/sentiment/` | GET | Sentiment analysis |

## 🎯 Frontend Integration

The backend is designed for seamless integration with the React frontend:

### Response Format
All responses follow a consistent structure:
```json
{
  "id": "unique_identifier",
  "keyField": "Display title/name",
  "sub": "Subtitle or summary",
  "data": { "field1": "value1", "field2": "value2" },
  "createdAt": "ISO 8601 timestamp"
}
```

### CORS Configuration
The API is configured to accept requests from:
- `http://localhost:5173` (React dev server)
- `http://localhost:3000` (Alternative frontend)
- Configure in `.env`: `CORS_ALLOWED_ORIGINS`

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test campaign_os.voters.tests

# With coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚢 Production Deployment

### Using Gunicorn + Nginx

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn campaign_os.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class sync

# For systemd service, see: deployment/campaign.service
# For Nginx configuration, see: deployment/nginx.conf
```

### Django Settings for Production

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECRET_KEY = 'your-secret-key'
DATABASES['default']['PASSWORD'] = 'secure-db-password'
```

## 📈 Performance Optimization

- **Database Indexes**: Strategic indexes on frequently queried fields
- **Select Related**: Foreign key optimization in queries
- **Prefetch Related**: Reverse relation optimization
- **Pagination**: Default 50 items per page
- **Caching**: Ready for Redis integration

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check MySQL is running
sudo service mysql status

# Create database if not exists
mysql -u root -p -e "CREATE DATABASE campaign_os;"
```

### Migration Issues
```bash
# Reset migrations (development only!)
python manage.py migrate zero

# Reapply all migrations
python manage.py migrate
```

### CORS Errors
```bash
# Update CORS_ALLOWED_ORIGINS in .env
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://yourdomain.com
```

##  📚 Documentation

- **API Docs**: See `API_DOCUMENTATION.md` (comprehensive guide)
- **Swagger UI**: Auto-generated at `/api/docs/`
- **ReDoc**: Auto-generated at `/api/redoc/`
- **Database Schema**: Models defined in each app's `models.py`

## 🛣️ Development Roadmap

- [ ] WebSocket support for real-time updates
- [ ] Advanced GIS/location-based queries
- [ ] Bulk import from CSV/Excel
- [ ] Report generation (PDF)
- [ ] Mobile app API (with additional endpoints)
- [ ] Advanced analytics with ML predictions
- [ ] Multi-language support (i18n)

## 📝 Code Standards

- **Style**: PEP 8
- **Type Hints**: Used throughout
- **Docstrings**: Google style
- **Testing**: Minimum 80% coverage
- **Git**: Conventional commits

## 🤝 Contributing

1. Create a feature branch: `git checkout -b feature/xyz`
2. Write tests for new code
3. Follow PEP 8 style guide
4. Commit with meaningful messages
5. Push and create a Pull Request

## 📞 Support

For questions, issues, or suggestions:
- Check API_DOCUMENTATION.md
- Review Django REST Framework docs
- Check Django official documentation

---

**Built with Django + DRF + MariaDB for Election Campaign Management**

*Last Updated: March 2026*
