from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from ..models import Profile, ReportRun
from ..schemas import ProfileCreate
from .normalization import normalize_text


def normalized_identity(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = normalize_text(value).lower()
    return normalized or None


def list_profiles(db: Session, query: str | None) -> list[Profile]:
    stmt = select(Profile).order_by(Profile.name.asc()).limit(20)
    if query:
        normalized_query = f"%{normalized_identity(query)}%"
        stmt = (
            select(Profile)
            .where(or_(Profile.normalized_name.like(normalized_query), Profile.name.ilike(f"%{query}%")))
            .order_by(Profile.name.asc())
            .limit(20)
        )
    return list(db.scalars(stmt))


def create_profile(db: Session, payload: ProfileCreate) -> Profile:
    profile = Profile(
        name=normalize_text(payload.name),
        email=normalize_text(payload.email) or None,
        normalized_name=normalized_identity(payload.name) or "",
        normalized_email=normalized_identity(payload.email),
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def get_profile(db: Session, profile_id: int) -> Profile | None:
    return db.get(Profile, profile_id)


def get_history(
    db: Session,
    profile_id: int,
    zone_query: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> tuple[list[ReportRun], int]:
    stmt = select(ReportRun).where(ReportRun.profile_id == profile_id)
    count_stmt = select(func.count()).select_from(ReportRun).where(ReportRun.profile_id == profile_id)
    if zone_query:
        normalized_zone = f"%{normalize_text(zone_query).lower()}%"
        stmt = stmt.where(ReportRun.normalized_zone_name.like(normalized_zone))
        count_stmt = count_stmt.where(ReportRun.normalized_zone_name.like(normalized_zone))
    if date_from:
        stmt = stmt.where(ReportRun.created_at >= date_from)
        count_stmt = count_stmt.where(ReportRun.created_at >= date_from)
    if date_to:
        inclusive = date_to.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=UTC)
        stmt = stmt.where(ReportRun.created_at <= inclusive)
        count_stmt = count_stmt.where(ReportRun.created_at <= inclusive)
    stmt = stmt.order_by(ReportRun.created_at.desc()).limit(100)
    return list(db.scalars(stmt)), db.scalar(count_stmt) or 0

