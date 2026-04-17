# HNG Internship Stage 1 — Profile Intelligence Service API

A REST API that enriches a name using three external APIs (Genderize, Agify, Nationalize), stores the result in a database, and exposes endpoints to retrieve, filter, and delete profiles.

---

## Tech Stack
- Python 3.11 / Django
- SQLite (development) 
- django-cors-headers
- Deployed on Railway

---

## Endpoints

### POST /api/profiles
Create a profile. Idempotent — returns existing profile if name already exists.

**Request:**
```json
{ "name": "ella" }
```

**Response (201):**
```json
{
  "status": "success",
  "data": {
    "id": "uuid-v7-here",
    "name": "ella",
    "gender": "female",
    "gender_probability": 0.99,
    "sample_size": 1234,
    "age": 46,
    "age_group": "adult",
    "country_id": "NG",
    "country_probability": 0.85,
    "created_at": "2026-04-01T12:00:00Z"
  }
}
```

### GET /api/profiles
List all profiles. Optional filters: `gender`, `country_id`, `age_group`

### GET /api/profiles/{id}
Get a single profile by ID.

### DELETE /api/profiles/{id}
Delete a profile. Returns 204 No Content.

---

## Setup
```bash
git clone https://github.com/anulusdev/hng-stage1.git
cd hng-stage1
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

---

## Live API
```
https://YOURAPP.up.railway.app
```