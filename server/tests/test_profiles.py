from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import Base
from app.schemas import ProfileCreate
from app.services.profiles import create_profile


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

