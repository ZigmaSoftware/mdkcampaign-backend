# Campaign OS - Election Campaign Management System Backend

A production-grade Django REST Framework backend for a comprehensive election campaign management platform.

## 🎯 Overview

Campaign OS is a sophisticated backend system designed to manage all aspects of a political election campaign:

- **Geographic Hierarchy**: Country → State → District → Constituency → Ward → Booth
- **Voter Management**: Contact tracking, sentiment analysis, surveys, feedback
- **Volunteer Management**: Task assignment, attendance, performance metrics
- **Campaign Events**: Rallies, meetings, door-to-door drives with attendance tracking
- **Analytics**: Real-time dashboards, sentiment distribution, coverage metrics
- **RBAC**: Role-based access control with hierarchical permissions
- **Elections**: Election metadata, opinion polls, poll questions and responses

## 🏗️ Architecture

### Project Structure
```
campaign_backend/
├── campaign_os/
│   ├── settings.py           # Django settings
│   ├── urls.py               # Main URL routing
│   ├── wsgi.py               # WSGI config
│   ├── core/                 # Core utilities and models
│   ├── accounts/             # User authentication and RBAC
│   ├── masters/              # Geographic and master data
│   ├── voters/               # Voter management
│   ├── volunteers/           # Volunteer management
│   ├── campaigns/            # Campaign events
│   ├── elections/            # Election metadata and polls
│   └── analytics/            # Dashboard and analytics
├── manage.py
├── pyproject.toml            # Python dependencies (uv)
├── .env.example              # Environment template
└── API_DOCUMENTATION.md      # This file
```

### Tech Stack
- **Framework**: Django 5.0+ with Django REST Framework 3.14+
- **Database**: MariaDB (MySQL compatible)
- **Authentication**: JWT (via simplejwt)
- **Package Manager**: uv (fast Python package manager)
- **API Documentation**: drf-spectacular (OpenAPI 3.0)

## 🚀 Quick Start

### 1. Install Python and uv

```bash
# On Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows (PowerShell)
powershell -ExecutionPolicy BypassUser -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Clone and Setup

```bash
cd /mnt/personal/election/campaign_backend

# Create virtual environment
uv venv

# Activate (Linux/Mac)
source .venv/bin/activate
# Or on Windows
.venv\Scripts\activate

# Install dependencies
uv sync
```

### 3. Create Database

```bash
# Using MySQL CLI
mysql -u root -p

CREATE DATABASE campaign_os CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'campaign_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON campaign_os.* TO 'campaign_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 4. Configure Environment

```bash
# Copy and edit .env
cp .env.example .env

# Edit .env with your settings:
# - DB_USER, DB_PASSWORD
# - SECRET_KEY, JWT_SIGNING_KEY
# - ALLOWED_HOSTS
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Load Initial Data (Optional)

```bash
python manage.py loaddata initial_data
```

### 8. Run Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

### 9. Access API

- **API Docs (Swagger)**: http://localhost:8000/api/docs/
- **API Docs (ReDoc)**: http://localhost:8000/api/redoc/
- **Admin Panel**: http://localhost:8000/admin/

## 📡 API Endpoints

### Authentication

#### Login
```
POST /api/v1/auth/login/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Get Current User
```
GET /api/v1/auth/users/me/
Authorization: Bearer {access_token}
```

#### Change Password
```
POST /api/v1/auth/users/change-password/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "old_password": "current_password",
  "new_password": "new_password",
  "new_password_confirm": "new_password"
}
```

### Masters (Geographic & Master Data)

#### List Districts
```
GET /api/v1/masters/districts/?state=1
Authorization: Bearer {access_token}

Response:
[
  {
    "id": 1,
    "name": "Erode",
    "code": "ERD",
    "state": 1,
    "state_name": "Tamil Nadu",
    "constituencies_count": 2,
    "booths_count": 274
  }
]
```

#### Get District Details with Constituencies
```
GET /api/v1/masters/districts/1/
GET /api/v1/masters/districts/1/constituencies/
```

#### List Constituencies
```
GET /api/v1/masters/constituencies/?district=1&election_type=assembly
```

#### List Wards
```
GET /api/v1/masters/wards/?constituency=100
```

#### List and Manage Booths
```
GET /api/v1/masters/booths/?ward=1&status=pending
POST /api/v1/masters/booths/         # Create booth
PUT /api/v1/masters/booths/{id}/     # Update booth
PATCH /api/v1/masters/booths/{id}/   # Partial update
DELETE /api/v1/masters/booths/{id}/  # Delete booth

GET /api/v1/masters/booths/{id}/voters/        # Voters in booth
POST /api/v1/masters/booths/{id}/assign_agent/ # Assign agent
GET /api/v1/masters/booths/{id}/nearby/        # Nearby booths
```

#### Parties and Candidates
```
GET /api/v1/masters/parties/
GET /api/v1/masters/parties/{id}/candidates/  # Candidates of party
GET /api/v1/masters/candidates/?constituency=100&is_incumbent=true
```

### Voters

#### List Voters
```
GET /api/v1/voters/voters/?booth=1&sentiment=positive&is_contacted=false
Authorization: Bearer {access_token}
```

#### Create Voter
```
POST /api/v1/voters/voters/
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "name": "John Doe",
  "voter_id": "A1234567",
  "phone": "9876543210",
  "booth": 1,
  "ward": 1,
  "address": "123 Main Street",
  "gender": "m",
  "sentiment": "neutral"
}
```

#### Get Voters by Criteria
```
GET /api/v1/voters/voters/by_booth/?booth_id=1
GET /api/v1/voters/voters/by_constituency/?constituency_id=100
GET /api/v1/voters/voters/by_sentiment/?sentiment=positive
GET /api/v1/voters/voters/uncontacted/
```

#### Mark Voter as Contacted
```
POST /api/v1/voters/voters/{id}/mark_contacted/
Authorization: Bearer {access_token}
```

#### Voter Contact History
```
GET /api/v1/voters/voters/{id}/contact_history/
POST /api/v1/voters/contacts/
Content-Type: application/json

{
  "voter": 1,
  "method": "phone",
  "duration_minutes": 5,
  "notes": "Interested in scheme details",
  "sentiment_after": "positive"
}
```

#### Voter Surveys
```
POST /api/v1/voters/surveys/
{
  "voter": 1,
  "survey_type": "opinion_poll",
  "responses": {
    "q1": "candidate_a",
    "q2": "development",
    "q3": "very_likely"
  },
  "score": 85
}

GET /api/v1/voters/surveys/?voter=1&survey_type=opinion_poll
```

#### Voter Feedback/Grievances
```
POST /api/v1/voters/feedbacks/
{
  "voter": 1,
  "feedback_type": "complaint",
  "subject": "Pothole on Main Street",
  "description": "Large pothole near booth 5",
  "issue": 3
}

GET /api/v1/voters/feedbacks/?status=new&issue=3

# Assign feedback
POST /api/v1/voters/feedbacks/{id}/assign/
{
  "assigned_to_id": 5
}

# Resolve feedback
POST /api/v1/voters/feedbacks/{id}/resolve/
{
  "resolution": "Pothole was repaired on 2026-03-20"
}
```

### Volunteers

#### List Volunteers
```
GET /api/v1/volunteers/volunteers/?booth=1&status=active
Authorization: Bearer {access_token}
```

#### Assign Tasks
```
POST /api/v1/volunteers/tasks/
{
  "volunteer": 1,
  "title": "Contact voters in Ward 5",
  "assignment_type": "voter_contact",
  "target_count": 500,
  "due_date": "2026-03-22",
  "priority": 1
}

# Get volunteer tasks
GET /api/v1/volunteers/tasks/?volunteer=1&status=pending
```

### Campaigns

#### Create Event
```
POST /api/v1/campaigns/events/
{
  "title": "Community Rally at Town Square",
  "event_type": "rally",
  "constituency": 100,
  "scheduled_date": "2026-03-22",
  "location": "Town Square, Erode",
  "expected_attendees": 1000
}

GET /api/v1/campaigns/events/?constituency=100&event_type=rally&status=planned
```

### Elections & Polls

#### Election Info
```
GET /api/v1/elections/elections/?state=1&election_type=assembly

GET /api/v1/elections/elections/{id}/
```

#### Opinion Polls
```
POST /api/v1/elections/polls/
{
  "election": 1,
  "name": "Exit Poll - Constituency 100",
  "constituency": 100,
  "sample_size": 5000,
  "poll_date_start": "2026-03-22",
  "poll_date_end": "2026-03-23"
}

GET /api/v1/elections/polls/?constituency=100
```

#### Record Poll Responses
```
POST /api/v1/elections/poll-responses/
{
  "poll": 1,
  "question": 5,
  "voter": 100,
  "response_text": "Candidate A"
}
```

### Analytics

#### Dashboard Statistics
```
GET /api/v1/analytics/dashboard/?constituency_id=100
Authorization: Bearer {access_token}

Response:
{
  "total_voters": 242185,
  "voters_contacted": 164365,
  "voters_by_sentiment": {
    "positive": 98500,
    "neutral": 45200,
    "negative": 15200,
    "undecided": 5465
  },
  "total_booths": 274,
  "booths_assigned": 256,
  "active_volunteers": 1248,
  "total_events": 42,
  "completed_events": 18
}
```

#### Booth Statistics
```
GET /api/v1/analytics/booths/?constituency_id=100

Response:
[
  {
    "id": 1,
    "name": "School XYZ",
    "number": "001",
    "total_voters": 885,
    "voters_contacted": 600,
    "coverage_percentage": 67.8
  }
]
```

#### Constituency Statistics
```
GET /api/v1/analytics/constituencies/
```

#### Volunteer Performance
```
GET /api/v1/analytics/volunteers/

Response:
[
  {
    "id": 1,
    "user__first_name": "Raj",
    "booth__name": "School ABC",
    "voters_contacted": 450,
    "performance_score": 85.5
  }
]
```

#### Sentiment Distribution
```
GET /api/v1/analytics/sentiment/?constituency_id=100
```

#### Geographic Coverage
```
GET /api/v1/analytics/coverage/

Response:
[
  {
    "id": 1,
    "name": "Erode",
    "total_booths": 274,
    "assigned_booths": 256,
    "total_voters": 242185,
    "contacted_voters": 164365
  }
]
```

## 🔐 Authentication & Authorization

### JWT Tokens

- **Access Token**: Short-lived (24 hours), used for API requests
- **Refresh Token**: Long-lived (7 days), used to get new access tokens

### Roles

1. **Admin**: Full system access
2. **District Head**: Access to all data in district  
3. **Constituency Manager**: Access limited to constituency
4. **Volunteer**: Limited access to own tasks and voter contact
5. **Analyst**: Read-only access to analytics
6. **Observer**: Limited read-only access

### Access Control Rules

```python
# User can access data based on hierarchy
user.has_access_to_district(district)        # Check district access
user.has_access_to_constituency(constituency) # Check constituency access
user.get_accessible_districts()               # Get all accessible districts
```

## 📊 Frontend Integration

### Response Format Compatibility

The backend provides standard REST responses. For frontend compatibility, responses are structured as:

```json
{
  "id": "...",
  "keyField": "Booth 001 – School XYZ",
  "sub": "Modakkurichi · 885 voters · Agent: Raj Kumar",
  "data": {
    "number": "001",
    "name": "School XYZ",
    "area": "Modakkurichi",
    "voters": "885",
    "agent": "Raj Kumar",
    "status": "working"
  },
  "createdAt": "2026-03-20T10:30:00Z"
}
```

### Naming Conventions

- **Districts** → `booths` (Geographic areas)
- **Booths** → `booth` (Polling stations)
- **Voters** → `voter` (Individual entries)
- **Volunteers** → `volunteer` (Campaign workers)
- **Events** → `event` (Campaign events)

## 🔧 Configuration

### Environment Variables

```env
# Core Django
DEBUG=True
SECRET_KEY=your-secret-key

# Database
DB_NAME=campaign_os
DB_USER=campaign_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=3306

# JWT
JWT_SIGNING_KEY=your-jwt-key

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173

# Logging
LOG_LEVEL=INFO
```

### Database Indexing

The system includes strategic indexes for optimal query performance:

- Booth: booth_id, status, sentiment, location
- Voter: booth_id, phone, sentiment, is_contacted, created_at
- Constituency: district_id, election_type
- User: phone, role, district_id

## 📈 Performance Optimization

### Query Optimization

- Uses `select_related()` for foreign keys
- Uses `prefetch_related()` for reverse relations
- Implements pagination (default 50 items per page)
- Supports filtering and searching

### Database Optimization

- Proper indexing on frequently queried fields
- Optimized for O(1) lookups on geographic hierarchy
- Denormalizes voter count on booth for fast stats

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test campaign_os.voters

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

## 🚢 Deployment

### Production Checklist

```bash
# 1. Update settings for production
export DEBUG=False
export ALLOWED_HOSTS=yourdomain.com
export SECRET_KEY=your-production-secret-key

# 2. Run migrations
python manage.py migrate --noinput

# 3. Collect static files
python manage.py collectstatic --noinput

# 4. Use production server (gunicorn)
gunicorn campaign_os.wsgi:application --bind 0.0.0.0:8000

# 5. Setup reverse proxy (Nginx)
# See nginx_config.conf
```

## 📝 API Documentation

Full OpenAPI 3.0 documentation available at:
- Swagger UI: `/api/docs/`
- ReDoc: `/api/redoc/`
- OpenAPI Schema: `/api/schema/`

## 🤝 Contributing

1. Follow PEP 8 style guide
2. Write tests for new features
3. Create models with proper relationships and indexes
4. Add serializers for all models
5. Update documentation

## 📄 License

Proprietary - Election Campaign Management System

## 📞 Support

For issues or questions, contact the development team.
