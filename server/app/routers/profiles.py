from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import HistoryResponse, ProfileCreate, ProfileRead
from ..services.profiles import create_profile, get_history, list_profiles

router = APIRouter(prefix="/profiles", tags=["profiles"])


@router.get("", response_model=list[ProfileRead])
def search_profiles(query: str | None = Query(default=None), db: Session = Depends(get_db)) -> list[ProfileRead]:
    return list_profiles(db, query)


@router.post("", response_model=ProfileRead, status_code=201)
def create_profile_route(payload: ProfileCreate, db: Session = Depends(get_db)) -> ProfileRead:
    try:
        return create_profile(db, payload)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="A profile with that name or email already exists.") from exc


@router.get("/{profile_id}/history", response_model=HistoryResponse)
def profile_history(
    profile_id: int,
    zone: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    items, total = get_history(db, profile_id, zone, date_from, date_to, page, page_size)
    total_pages = max((total + page_size - 1) // page_size, 1)
    return HistoryResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)
