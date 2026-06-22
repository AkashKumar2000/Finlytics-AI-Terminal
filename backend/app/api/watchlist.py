from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import User, WatchlistItem
from app.schemas.research import WatchlistAddRequest, WatchlistResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.get("/", response_model=list[WatchlistResponse])
async def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all watchlist items for the current org."""
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.org_id == current_user.org_id
        )
    )
    return result.scalars().all()


@router.post("/", response_model=WatchlistResponse, status_code=201)
async def add_to_watchlist(
    payload: WatchlistAddRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a company to the org's watchlist."""
    # Check for duplicate within the same org
    existing = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.org_id == current_user.org_id,
            WatchlistItem.symbol == payload.symbol.upper(),
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{payload.symbol.upper()} is already in the watchlist",
        )

    item = WatchlistItem(                       # Inserting into the database table WatchItem
        symbol=payload.symbol.upper(),
        company_name=payload.company_name,
        notes=payload.notes,
        org_id=current_user.org_id,
        added_by=current_user.id,
    )
    db.add(item)
    await db.flush()
    return item

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a company from the watchlist. Tenant-scoped."""
    result = await db.execute(
        select(WatchlistItem).where(
            WatchlistItem.id == item_id,
            WatchlistItem.org_id == current_user.org_id,
        )
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Watchlist item not found")

    await db.delete(item)




