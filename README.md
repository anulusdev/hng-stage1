# Intelligence Query Engine - Insighta Labs (HNG Stage 2)

## Overview
This project is a production-ready backend API built for **Insighta Labs**, a demographic intelligence company. It upgrades a basic data-collection API into a fully queryable Intelligence Engine. 

Clients (marketing teams, product managers, and growth analysts) can use this API to effectively segment users, combine multiple demographic conditions, sort and paginate large datasets, and execute complex queries using plain English.

## Key Features
* **Advanced Combinable Filtering:** Filter profiles by exact matches or thresholds (e.g., age ranges, probability scores).
* **Dynamic Sorting & Pagination:** Sort data by specific fields (ascending or descending) and paginate through results to handle large datasets efficiently.
* **Natural Language Query (NLP) Engine:** A rule-based English parser that translates plain text queries (e.g., *"young males from nigeria"*) into complex database filters.
* **Idempotent Data Seeding:** Safely bulk-loads demographic data from a JSON file into the database without creating duplicate records.
* **Standardized Error Handling:** Consistent JSON error structures for 400, 422, 404, and 500 level HTTP responses.

---

## Database Schema
The primary `profiles` table is strictly structured as follows:

| Field | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID v7 | Primary key, time-ordered |
| `name` | VARCHAR | Person's full name (UNIQUE) |
| `gender` | VARCHAR | "male" or "female" |
| `gender_probability` | FLOAT | Confidence score |
| `age` | INT | Exact age |
| `age_group` | VARCHAR | child, teenager, adult, senior |
| `country_id` | VARCHAR(2) | ISO 3166-1 alpha-2 code (e.g., NG, BJ) |
| `country_name` | VARCHAR | Full country name |
| `country_probability` | FLOAT | Confidence score |
| `created_at` | TIMESTAMP | Auto-generated in UTC ISO 8601 |

---

## API Documentation

### 1. Advanced Filtering, Sorting, and Pagination
**Endpoint:** `GET /api/profiles`

Retrieve a paginated list of profiles. All filters can be combined, and results will strictly match all provided conditions.

**Supported Query Parameters:**
* **Filters:** `gender`, `age_group`, `country_id`
* **Ranges:** `min_age`, `max_age`
* **Thresholds:** `min_gender_probability`, `min_country_probability`
* **Sorting:** `sort_by` (age, created_at, gender_probability) & `order` (asc, desc)
* **Pagination:** `page` (default: 1), `limit` (default: 10, max: 50)

**Example Request:**
`/api/profiles?gender=male&country_id=NG&min_age=25&sort_by=age&order=desc&limit=5`

**Success Response (200 OK):**
```json
{
  "status": "success",
  "page": 1,
  "limit": 5,
  "total": 2026,
  "data": [
    {
      "id": "018f2a...",
      "name": "khaleed",
      "gender": "male",
      "age": 28,
      "age_group": "adult",
      "country_id": "NG",
      "country_name": "Nigeria"
    }
  ]
}
2. Natural Language Query Engine
Endpoint: GET /api/profiles/search

Interpret plain English strings and convert them into demographic filters using a rule-based parser. Standard pagination (page, limit) and sorting applies.

Example Request: /api/profiles/search?q=young males from nigeria

Recognized Mapping Rules:

"young males" → gender=male, min_age=16, max_age=24 (Note: "young" strictly maps to 16-24)

"females above 30" → gender=female, min_age=30

"people from angola" → country_id=AO

"adult males from kenya" → gender=male, age_group=adult, country_id=KE

Error Response (Unrecognized Query):

JSON
{
  "status": "error",
  "message": "Unable to interpret query"
}
3. Standard CRUD Operations
POST /api/profiles: Create a new profile by supplying a {"name": "..."} JSON body. Looks up demographic data via external APIs.

GET /api/profiles/{id}: Retrieve a full profile record by its UUID v7.

DELETE /api/profiles/{id}: Delete a profile (Returns 204 No Content).

Error Handling
Invalid requests gracefully return structured errors:

400 Bad Request: Missing or empty parameters.

422 Unprocessable Entity: Invalid parameter types (e.g., passing letters to an age query).

404 Not Found: Profile UUID does not exist.

Example Error Response:

JSON
{
  "status": "error",
  "message": "Invalid query parameters"
}
Local Setup & Seeding Instructions
1. Clone and Configure

Bash
git clone <your-repo-link>
cd <repository-folder>
python -m venv venv
source venv/bin/activate  # Or venv\Scripts\activate on Windows
pip install -r requirements.txt
2. Database Migration

Bash
python manage.py makemigrations
python manage.py migrate
3. Seed the Database
The project includes a custom management command to bulk-load the required 2,026 profiles from the provided JSON file. Place seed_profiles.json in the root directory and run:

Bash
python manage.py seed_profiles
(Note: This command is idempotent and will not duplicate records if run multiple times).

4. Run the Server

Bash
python manage.py runserver