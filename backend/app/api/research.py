from fastapi import APIRouter , Depends , HTTPException, Query , status 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select , desc

from app.database import get_db
from app.models import User , ResearchReport , AuditLog
from app.schemas.research import (
    ResearchQueryRequest,
    ResearchReportResponse,
    ResearchReportListResponse,
    ResearchUpdateRequest,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/research", tags=["Research"])

@router.get("/", response_model = list[ResearchReportListResponse])
async def list_reports(
    current_user : User = Depends(get_current_user), 
    db : AsyncSession = Depends(get_db),
    skip : int = Query(0, ge=0),
    limit : int = Query(20, ge=1, le=100),
    tag: str | None= None ,
    search : str | None = None ,  ):

    """List research report for the current organization . Supports pagination , tag filter , search"""

    # Tenant -scoped query : only this organization reports
    query = select(ResearchReport).where(ResearchReport.org_id == current_user.org_id)

    if search :
        query = query.where(
            ResearchReport.title.ilike(f"%{search}%")   # ilike for case insensitive
            | ResearchReport.query.ilike(f"%{search}%")
        )
    
    query = query.order_by(desc(ResearchReport.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/{report_id}", response_model= ResearchReportResponse)
async def get_report(
    report_id : str, 
    current_user : User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    """ Get a single research report . Tenant-scoped"""
    result = await db.execute(
        select(ResearchReport).where(
            ResearchReport.id == report_id,
            ResearchReport.org_id == current_user.org_id,  # Tenant isolation
        )
    )
    report = result.scalar_one_or_none()
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/query", response_model= ResearchReportResponse, status_code= 201)
async def create_research(
    payload:  ResearchQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    """Submit a new research query. Runs the AI agent and stores results.

    This is the main endpoint — it will call the AI orchestration layer
    (implemented in Day 2).
    """

    # For now, create a placeholder report. Day 2 will wire in the AI agent.

    report = ResearchReport(
        title= payload.query[:100],
        query= payload.query,
        result_data = {"message": "AI processing will be connected in the AI layer"},
        sources= [], 
        tags =[],
        status = "pending", 
        org_id=current_user.org_id,
        created_by=current_user.id,
    )
    db.add(report)
    await db.flush()

    # Audit log
    audit = AuditLog(
        action="research.created",
        entity_type="research_report",
        entity_id=report.id,
        details={"query": payload.query},
        user_id=current_user.id,
        org_id=current_user.org_id,
    )

    db.add(audit)

    return report



@router.put("/{report_id}", response_model=ResearchReportResponse)
async def update_report(
    report_id: str,
    payload: ResearchUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a report's title or tags. Tenant-scoped."""
    result = await db.execute(
        select(ResearchReport).where(
            ResearchReport.id == report_id,
            ResearchReport.org_id == current_user.org_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if payload.title is not None:
        report.title = payload.title
    if payload.tags is not None:
        report.tags = payload.tags

    db.add(report)
    return report


@router.delete("/{report_id}" , status_code= status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    """Delete a research report . Tenant-scoped"""

    result = await db.execute(
        select(ResearchReport).where(
            ResearchReport.id == report_id, 
            ResearchReport.org_id == current_user.org_id,
        )
    )

    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    await db.delete(report)

    # Audit log
    audit = AuditLog(
        action="research.deleted",
        entity_type="research_report",
        entity_id=report_id,
        user_id=current_user.id,
        org_id=current_user.org_id,
    )

    db.add(audit)
