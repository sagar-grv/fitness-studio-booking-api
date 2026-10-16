"""Class booking endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Booking, FitnessClass, User
from ..schemas import BookingRequest, BookingResponse
from ..timeutils import IST_ZONE, serialize_ist

logger = logging.getLogger(__name__)

router = APIRouter(tags=["bookings"])


def _to_response(booking: Booking, cls: FitnessClass) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        class_id=cls.id,
        class_name=cls.name,
        class_dateTime=cls.date_time,
        instructor=cls.instructor,
        client_name=booking.client_name,
        client_email=booking.client_email,
        booked_at=serialize_ist(booking.booked_at.replace(tzinfo=IST_ZONE))
        if booking.booked_at.tzinfo is None
        else serialize_ist(booking.booked_at),
    )


@router.post(
    "/book", response_model=BookingResponse, status_code=status.HTTP_201_CREATED
)
def book_class(
    body: BookingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Book a slot in a class. Requires authentication.

    Validates that the class exists, has not already started, still has
    free slots, and that the user has not already booked it. The slot
    decrement is a single atomic UPDATE, so concurrent requests cannot
    overbook the class.
    """
    cls = db.get(FitnessClass, body.class_id)
    if cls is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Class not found"
        )
    if cls.date_time <= serialize_ist(datetime.now(IST_ZONE)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This class has already started or ended",
        )

    duplicate = (
        db.query(Booking)
        .filter(Booking.user_id == current_user.id, Booking.class_id == cls.id)
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already booked this class",
        )

    # Atomic decrement: only succeeds while a slot is actually free.
    result = db.execute(
        update(FitnessClass)
        .where(FitnessClass.id == cls.id, FitnessClass.available_slots > 0)
        .values(available_slots=FitnessClass.available_slots - 1)
    )
    if result.rowcount == 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No slots available for this class",
        )

    booking = Booking(
        user_id=current_user.id,
        class_id=cls.id,
        client_name=body.client_name.strip(),
        client_email=body.client_email.lower(),
    )
    db.add(booking)
    try:
        db.commit()
    except IntegrityError:  # concurrent duplicate booking raced past the check
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already booked this class",
        )
    db.refresh(booking)
    db.refresh(cls)
    logger.info(
        "user %s booked class %s (booking %s)", current_user.id, cls.id, booking.id
    )
    return _to_response(booking, cls)


@router.get("/bookings", response_model=list[BookingResponse])
def list_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """View all bookings made by the authenticated user, newest first."""
    rows = (
        db.query(Booking, FitnessClass)
        .join(FitnessClass, Booking.class_id == FitnessClass.id)
        .filter(Booking.user_id == current_user.id)
        .order_by(Booking.booked_at.desc())
        .all()
    )
    return [_to_response(booking, cls) for booking, cls in rows]
