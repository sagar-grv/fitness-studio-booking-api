"""Seed the database with sample fitness classes.

Usage:
    python seed.py
"""

from datetime import datetime, timedelta

from app.database import Base, SessionLocal, engine
from app.models import FitnessClass
from app.timeutils import IST_ZONE, serialize_ist

SAMPLE_CLASSES = [
    ("Yoga Flow", "John Doe", 20, 1, 10, 0),
    ("Zumba Party", "Priya Sharma", 25, 1, 18, 30),
    ("HIIT Session", "Jane Smith", 15, 2, 8, 0),
    ("Pilates Core", "Arjun Mehta", 12, 2, 17, 0),
    ("Spin Class", "Neha Verma", 18, 3, 7, 30),
    ("Strength Training", "Rahul Kapoor", 10, 3, 19, 0),
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(FitnessClass).count() > 0:
            print("Classes already exist - skipping seed.")
            return
        now = datetime.now(IST_ZONE).replace(second=0, microsecond=0)
        for name, instructor, slots, days, hour, minute in SAMPLE_CLASSES:
            start = (now + timedelta(days=days)).replace(hour=hour, minute=minute)
            db.add(
                FitnessClass(
                    name=name,
                    date_time=serialize_ist(start),
                    instructor=instructor,
                    total_slots=slots,
                    available_slots=slots,
                )
            )
        db.commit()
        print(f"Seeded {len(SAMPLE_CLASSES)} sample classes (times in IST).")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
