"""Class listing and creation endpoints."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import IST
from ..database import get_db
from ..models import FitnessClass, User
from ..schemas import ClassCreateRequest, ClassResponse
from ..timeutils import IST_ZONE, convert_for_output, serialize_ist

logger = logging.getLogger(__name__)

router = APIRouter(tags=["classes"])


def _to_response(cls: FitnessClass, timezone: str) -> ClassResponse:
    return ClassResponse(
        id=cls.id,
        name=cls.name,
        dateTime=convert_for_output(cls.date_time, timezone),
        instructor=cls.instructor,
        availableSlots=cls.available_slots,
        totalSlots=cls.total_slots,
    )


@router.get("/classes", response_model=list[ClassResponse])
def list_classes(
    timezone: str = Query(
        default=IST,
        description="IANA timezone for the returned class times (stored in IST)",
    ),
    db: Session = Depends(get_db),
):
    """Fetch all upcoming fitness classes, soonest first.

    Times are stored in IST and converted to the requested timezone.
    """
    now_ist = serialize_ist(datetime.now(IST_ZONE))
    classes = (
        db.query(FitnessClass)
        .filter(FitnessClass.date_time >= now_ist)
        .order_by(FitnessClass.date_time.asc())
        .all()
    )
    return [_to_response(c, timezone) for c in classes]


@router.post(
    "/classes", response_model=ClassResponse, status_code=status.HTTP_201_CREATED
)
def create_class(
    body: ClassCreateRequest,
    timezone: str = Query(default=IST),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new fitness class. Requires authentication.

    The supplied dateTime may carry any UTC offset; it is normalized to
    IST before storage.
    """
    cls = FitnessClass(
        name=body.name.strip(),
        date_time=serialize_ist(body.dateTime),
        instructor=body.instructor.strip(),
        total_slots=body.availableSlots,
        available_slots=body.availableSlots,
    )
    db.add(cls)
    db.commit()
    db.refresh(cls)
    logger.info("user %s created class %s (%s)", current_user.id, cls.id, cls.name)
    return _to_response(cls, timezone)
