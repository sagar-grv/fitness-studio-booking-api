"""Pydantic request/response schemas with validation."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until the access token expires


class RefreshRequest(BaseModel):
    refresh_token: str


class ClassCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    dateTime: datetime  # ISO-8601; naive values are treated as IST
    instructor: str = Field(..., min_length=1, max_length=100)
    availableSlots: int = Field(..., ge=1)


class ClassResponse(BaseModel):
    id: int
    name: str
    dateTime: str
    instructor: str
    availableSlots: int
    totalSlots: int


class BookingRequest(BaseModel):
    class_id: int
    client_name: str = Field(..., min_length=1, max_length=100)
    client_email: EmailStr


class BookingResponse(BaseModel):
    id: int
    class_id: int
    class_name: str
    class_dateTime: str
    instructor: str
    client_name: str
    client_email: str
    booked_at: str
