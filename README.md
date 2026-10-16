# Fitness Studio Booking API

A backend Booking API for a fictional fitness studio, built with **Python + FastAPI**. Users sign up and log in with JWT authentication, view upcoming classes, create new classes, book available slots, and view their own bookings. All class times are stored in **IST (Asia/Kolkata)** and can be returned in any timezone.

## Features

- User authentication: sign up, log in, JWT access + refresh tokens with expiry
- Create and list fitness classes (Yoga, Zumba, HIIT, ...)
- Book class slots with overbooking protection (atomic slot deduction)
- View your own bookings
- Timezone management: times stored in IST, converted on output
- Request validation, error handling for missing fields and auth failures
- Request logging middleware
- Unit tests (pytest)
- Auto-generated Swagger docs at `/docs`

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** FastAPI
- **Database:** SQLite (via SQLAlchemy ORM)
- **Auth:** JWT (PyJWT), PBKDF2-HMAC-SHA256 password hashing

## Project Structure

```
├── app/
│   ├── main.py            # FastAPI app, middleware, router wiring
│   ├── config.py          # Settings (JWT, database URL, timezone)
│   ├── database.py        # Engine + session setup
│   ├── models.py          # SQLAlchemy models (User, FitnessClass, Booking)
│   ├── schemas.py         # Pydantic request/response validation
│   ├── auth.py            # Password hashing + JWT helpers
│   ├── timeutils.py       # IST storage and timezone conversion
│   └── routers/
│       ├── auth_routes.py # /signup, /login, /refresh
│       ├── classes.py     # GET/POST /classes
│       └── bookings.py    # POST /book, GET /bookings
├── tests/
│   └── test_api.py        # 13 unit tests
├── seed.py                # Sample class data
├── requirements.txt
└── README.md
```

## Setup Instructions

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd fitness-studio-booking-api

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. (Optional) Seed sample classes
python seed.py
```

## How to Run Locally

```bash
uvicorn app.main:app --reload
```

- API base URL: `http://127.0.0.1:8000`
- Interactive Swagger docs: `http://127.0.0.1:8000/docs`

To run the tests:

```bash
pip install pytest httpx
pytest -v
```

## API Usage

### 1. Sign up

```bash
curl -X POST http://127.0.0.1:8000/signup \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "password": "secret123"}'
```

Response:

```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. Log in

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "secret123"}'
```

### 3. Create a class (auth required)

```bash
curl -X POST http://127.0.0.1:8000/classes \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Yoga Flow",
    "dateTime": "2026-10-20T07:00:00+05:30",
    "instructor": "John Doe",
    "availableSlots": 20
  }'
```

Any UTC offset is accepted on input; the time is normalized to IST before storage.

### 4. List upcoming classes

```bash
curl http://127.0.0.1:8000/classes
```

Times are returned in IST by default. Pass an IANA timezone to convert:

```bash
curl "http://127.0.0.1:8000/classes?timezone=UTC"
```

### 5. Book a class (auth required)

```bash
curl -X POST http://127.0.0.1:8000/book \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "class_id": 1,
    "client_name": "Alice",
    "client_email": "alice@example.com"
  }'
```

The booking validates that the class exists, has not started, still has free slots, and that you have not already booked it. Slots are deducted atomically, so concurrent requests cannot overbook.

### 6. View your bookings (auth required)

```bash
curl http://127.0.0.1:8000/bookings \
  -H "Authorization: Bearer <access_token>"
```

### 7. Refresh an expired access token

```bash
curl -X POST http://127.0.0.1:8000/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | dev value | JWT signing key - always set in production |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `DATABASE_URL` | `sqlite:///./fitness_studio.db` | SQLAlchemy database URL |

## Design Notes

- **Timezone handling:** class times are stored as ISO-8601 strings normalized to IST (`Asia/Kolkata`). Naive input is assumed to be IST; offset-aware input is converted. Output converts to any requested IANA timezone.
- **Overbooking protection:** the slot decrement is a single conditional `UPDATE ... WHERE available_slots > 0`, which is atomic at the database level.
- **Passwords:** salted PBKDF2-HMAC-SHA256 (200,000 iterations), never stored in plain text.
