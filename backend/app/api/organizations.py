from fastapi import APIRouter , Depends , HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Organization , User
from app.schemas.organization import OrgResponse , OrgUpdateRequest, OrgMemberResponse
from app.api.deps import get_current_user, require_admin

router = APIRouter(prefix="/org", tags=["Organization"])

@router.get("/", response_model= OrgResponse)
async def get_my_org(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    """Get the current user's organization details."""
    result = await db.execute(
        select(Organization).where(Organization.id == current_user.org_id)
    )
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return org

@router.put("/", response_model = OrgResponse)
async def update_org(
    payload: OrgUpdateRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):

    """Update organization details , if you are ADMIN only"""

    result = await db.execute(
        select(Organization).where(Organization.id == admin.org_id)
    )
    org = result.scalar_one()

    if payload.name is not None:
        org.name = payload.name
    if payload.description is not None:
        org.description = payload.description

    db.add(org)
    return org

@router.get("/member", response_model= list[OrgMemberResponse])
async def list_members(
    current_user : User= Depends(get_current_user),
    db : AsyncSession = Depends(get_db),
):

    """List all member in the current user's organization"""

    result = await db.execute(
        select(User).where(User.org_id == current_user.org_id)
    )

    return result.scalars().all()


@router.get("/invite-code")
async def get_invite_code(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get the org's invite code. Admin only."""
    result = await db.execute(
        select(Organization).where(Organization.id == admin.org_id)
    )
    org = result.scalar_one()
    return {"invite_code": org.invite_code}
