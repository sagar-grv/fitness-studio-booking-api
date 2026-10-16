"""Unit tests for the Fitness Studio Booking API.

Run with:  pytest -v
Uses a temporary SQLite database so the dev database is never touched.
"""

import os
import tempfile

import pytest
from fastapi.testclient import TestClient

# Point the app at a throwaway database before importing it.
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_db.name}"

from app.main import app  # noqa: E402

client = TestClient(app)

USER = {"name": "Alice", "email": "alice@example.com", "password": "secret123"}


@pytest.fixture(scope="module", autouse=True)
def token():
    """Sign up once per test module and hand out an auth header."""
    resp = client.post("/signup", json=USER)
    assert resp.status_code == 201, resp.text
    access = resp.json()["access_token"]
    return {"Authorization": f"Bearer {access}"}


def _future_class(slots=2):
    return {
        "name": "Test Yoga",
        "dateTime": "2030-06-15T10:00:00+05:30",
        "instructor": "Test Instructor",
        "availableSlots": slots,
    }


def test_signup_and_login():
    resp = client.post(
        "/signup",
        json={"name": "Bob", "email": "bob@example.com", "password": "pass123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["access_token"] and body["refresh_token"]

    resp = client.post(
        "/login", json={"email": "bob@example.com", "password": "pass123"}
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


def test_signup_duplicate_email_rejected():
    resp = client.post("/signup", json=USER)
    assert resp.status_code == 409


def test_login_wrong_password_rejected():
    resp = client.post(
        "/login", json={"email": USER["email"], "password": "wrong-pass"}
    )
    assert resp.status_code == 401


def test_missing_fields_rejected():
    resp = client.post("/signup", json={"email": "noname@example.com"})
    assert resp.status_code == 422


def test_create_class_requires_auth():
    resp = client.post("/classes", json=_future_class())
    assert resp.status_code == 401


def test_create_and_list_classes(token):
    resp = client.post("/classes", json=_future_class(), headers=token)
    assert resp.status_code == 201, resp.text
    created = resp.json()
    # Stored in IST, so the +05:30 offset is preserved on output.
    assert created["dateTime"].endswith("+05:30")
    assert created["availableSlots"] == 2

    resp = client.get("/classes")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.json()]
    assert "Test Yoga" in names


def test_class_time_timezone_conversion():
    # 10:00 UTC should come back as 15:30 IST.
    payload = _future_class()
    payload["dateTime"] = "2030-06-15T10:00:00+00:00"
    resp = client.post("/classes", json=payload)
    # no auth -> 401; create via authed fixture path instead
    assert resp.status_code == 401


def test_timezone_conversion_authed(token):
    payload = _future_class()
    payload["name"] = "TZ Check"
    payload["dateTime"] = "2030-06-15T10:00:00+00:00"  # 10:00 UTC
    resp = client.post("/classes", json=payload, headers=token)
    assert resp.status_code == 201
    assert resp.json()["dateTime"] == "2030-06-15T15:30:00+05:30"

    resp = client.get("/classes", params={"timezone": "UTC"})
    match = [c for c in resp.json() if c["name"] == "TZ Check"]
    assert match and match[0]["dateTime"] == "2030-06-15T10:00:00+00:00"


def test_booking_flow_and_overbooking(token):
    resp = client.post("/classes", json=_future_class(slots=1), headers=token)
    class_id = resp.json()["id"]

    booking = {
        "class_id": class_id,
        "client_name": "Alice",
        "client_email": "alice@example.com",
    }
    resp = client.post("/book", json=booking, headers=token)
    assert resp.status_code == 201, resp.text
    assert resp.json()["class_id"] == class_id

    # Duplicate booking by the same user is rejected.
    resp = client.post("/book", json=booking, headers=token)
    assert resp.status_code == 409

    # A second user fills the last seat check: class had only 1 slot,
    # so another user's booking hits overbooking protection.
    client.post(
        "/signup",
        json={"name": "Carol", "email": "carol@example.com", "password": "pass123"},
    )
    resp = client.post(
        "/login", json={"email": "carol@example.com", "password": "pass123"}
    )
    carol = {"Authorization": f"Bearer {resp.json()['access_token']}"}
    resp = client.post(
        "/book",
        json={
            "class_id": class_id,
            "client_name": "Carol",
            "client_email": "carol@example.com",
        },
        headers=carol,
    )
    assert resp.status_code == 409  # no slots available

    # Slots were deducted: available went from 1 to 0.
    resp = client.get("/classes")
    cls = [c for c in resp.json() if c["id"] == class_id][0]
    assert cls["availableSlots"] == 0


def test_booking_requires_auth():
    resp = client.post(
        "/book",
        json={"class_id": 1, "client_name": "X", "client_email": "x@example.com"},
    )
    assert resp.status_code == 401


def test_booking_nonexistent_class(token):
    resp = client.post(
        "/book",
        json={"class_id": 99999, "client_name": "X", "client_email": "x@example.com"},
        headers=token,
    )
    assert resp.status_code == 404


def test_view_own_bookings_only(token):
    resp = client.get("/bookings", headers=token)
    assert resp.status_code == 200
    bookings = resp.json()
    assert len(bookings) >= 1
    assert all(b["client_email"] == "alice@example.com" for b in bookings)


def test_refresh_token_issues_new_pair():
    resp = client.post(
        "/login", json={"email": USER["email"], "password": USER["password"]}
    )
    refresh_token = resp.json()["refresh_token"]
    resp = client.post("/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert resp.json()["access_token"]

    # An access token must not work as a refresh token.
    access = client.post(
        "/login", json={"email": USER["email"], "password": USER["password"]}
    ).json()["access_token"]
    resp = client.post("/refresh", json={"refresh_token": access})
    assert resp.status_code == 401
