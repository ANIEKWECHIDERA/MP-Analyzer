from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.models import ReportRun
from app.schemas import ProfileCreate
from app.services.profiles import create_profile, get_history


def test_profile_creation_enforces_unique_name() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)
    db: Session = session()

    create_profile(db, ProfileCreate(name="Ada", email=None))

    try:
        create_profile(db, ProfileCreate(name="Ada", email=None))
    except Exception:
        assert True
    else:
        assert False


def test_history_is_paginated_to_ten_items() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine, expire_on_commit=False)
    db: Session = session()

    profile = create_profile(db, ProfileCreate(name="Grace", email=None))
    now = datetime.now(UTC)
    for index in range(12):
        db.add(
            ReportRun(
                profile_id=profile.id,
                zone_name=f"Zone {index}",
                normalized_zone_name=f"zone {index}",
                source_filename=f"file-{index}.xlsx",
                source_file_fingerprint=f"fp-{index}",
                status="completed",
                created_at=now - timedelta(minutes=index),
            )
        )
    db.commit()

    first_page, total = get_history(db, profile.id, None, None, None, 1, 10)
    second_page, _ = get_history(db, profile.id, None, None, None, 2, 10)

    assert total == 12
    assert len(first_page) == 10
    assert len(second_page) == 2
