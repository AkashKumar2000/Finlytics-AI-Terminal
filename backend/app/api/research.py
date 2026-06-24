import json
import asyncio
import logging
import textwrap
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db, AsyncSessionLocal
from app.models import User, ResearchReport, AuditLog
from app.schemas.research import (
    ResearchQueryRequest,
    ResearchReportResponse,
    ResearchReportListResponse,
    ResearchReportListPaginatedResponse,
    ResearchUpdateRequest,
)
from app.api.deps import get_current_user
from app.ai.agent import run_research_query

logger = logging.getLogger("research_api")

router = APIRouter(prefix="/research", tags=["Research"])


@router.get("/", response_model=ResearchReportListPaginatedResponse)
async def list_reports(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tag: str | None = None,
    search: str | None = None,
):
    """List research reports for the current org. Supports pagination, tag filter, search."""
    base = select(ResearchReport).where(
        ResearchReport.org_id == current_user.org_id
    )
    if search:
        base = base.where(
            ResearchReport.title.ilike(f"%{search}%")
            | ResearchReport.query.ilike(f"%{search}%")
        )

    count_result = await db.execute(
        select(func.count(ResearchReport.id)).where(
            ResearchReport.org_id == current_user.org_id,
            *(
                [ResearchReport.title.ilike(f"%{search}%") | ResearchReport.query.ilike(f"%{search}%")]
                if search else []
            ),
        )
    )
    total = count_result.scalar_one()

    result = await db.execute(
        base.order_by(desc(ResearchReport.created_at)).offset(offset).limit(limit)
    )
    reports = result.scalars().all()

    return {"reports": reports, "total": total}


@router.get("/{report_id}/export")
async def export_report_pdf(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export a research report as a PDF file."""
    result = await db.execute(
        select(ResearchReport).where(
            ResearchReport.id == report_id,
            ResearchReport.org_id == current_user.org_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    pdf_bytes = _generate_pdf(report)
    safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in (report.title or "report"))[:40]

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{safe_title}.pdf"'},
    )


@router.get("/{report_id}", response_model=ResearchReportResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single research report. Tenant-scoped."""
    result = await db.execute(
        select(ResearchReport).where(
            ResearchReport.id == report_id,
            ResearchReport.org_id == current_user.org_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.post("/query", response_model=ResearchReportResponse, status_code=201)
async def create_research(
    payload: ResearchQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a research query. Runs the AI agent synchronously and returns structured results."""
    report = ResearchReport(
        title=payload.query[:100],
        query=payload.query,
        result_data=None,
        sources=[],
        tags=[],
        status="processing",
        org_id=current_user.org_id,
        created_by=current_user.id,
    )
    db.add(report)
    await db.flush()

    audit = AuditLog(
        action="research.created",
        entity_type="research_report",
        entity_id=report.id,
        details={"query": payload.query},
        user_id=current_user.id,
        org_id=current_user.org_id,
    )
    db.add(audit)
    await db.flush()

    try:
        ai_result = await run_research_query(payload.query)
        report.title = ai_result.get("title", payload.query[:100])
        report.result_data = ai_result
        report.sources = ai_result.get("sources", [])
        report.status = "completed"
        report.tags = ai_result.get("companies_analyzed", [])
    except Exception as e:
        logger.error(f"AI agent failed: {e}", exc_info=True)
        report.result_data = {
            "title": "Analysis Error",
            "summary": f"The AI agent encountered an error: {str(e)}",
            "sections": [],
            "error": str(e),
        }
        report.status = "failed"

    db.add(report)
    return report


@router.post("/query/stream")
async def create_research_stream(
    payload: ResearchQueryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """SSE streaming endpoint. Emits progress events then the final report."""
    report = ResearchReport(
        title=payload.query[:100],
        query=payload.query,
        status="processing",
        org_id=current_user.org_id,
        created_by=current_user.id,
    )
    db.add(report)
    await db.flush()
    report_id = report.id
    org_id = current_user.org_id

    async def event_generator():
        yield f"data: {json.dumps({'type': 'status', 'message': 'Starting research analysis...', 'report_id': report_id})}\n\n"

        try:
            yield f"data: {json.dumps({'type': 'status', 'message': 'AI agent is analysing your query...'})}\n\n"

            ai_result = await run_research_query(payload.query)

            # Emit which tools were called (from intermediate steps recorded by the agent)
            for tc in ai_result.get("tool_calls", []):
                tool_name = tc.get("tool", "unknown")
                yield f"data: {json.dumps({'type': 'tool', 'message': f'Called tool: {tool_name}'})}\n\n"
                await asyncio.sleep(0)

            yield f"data: {json.dumps({'type': 'status', 'message': 'Synthesising results...'})}\n\n"

            async with AsyncSessionLocal() as save_db:
                res = await save_db.execute(
                    select(ResearchReport).where(
                        ResearchReport.id == report_id,
                        ResearchReport.org_id == org_id,
                    )
                )
                saved = res.scalar_one()
                saved.title = ai_result.get("title", payload.query[:100])
                saved.result_data = ai_result
                saved.sources = ai_result.get("sources", [])
                saved.status = "completed"
                saved.tags = ai_result.get("companies_analyzed", [])
                save_db.add(saved)
                await save_db.commit()

            yield f"data: {json.dumps({'type': 'result', 'report_id': report_id, 'data': ai_result})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'report_id': report_id})}\n\n"

        except Exception as e:
            logger.error(f"Streaming research failed: {e}", exc_info=True)
            async with AsyncSessionLocal() as save_db:
                res = await save_db.execute(
                    select(ResearchReport).where(ResearchReport.id == report_id)
                )
                saved = res.scalar_one_or_none()
                if saved:
                    saved.status = "failed"
                    saved.result_data = {"error": str(e)}
                    save_db.add(saved)
                    await save_db.commit()

            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


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


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a research report. Tenant-scoped."""
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

    audit = AuditLog(
        action="research.deleted",
        entity_type="research_report",
        entity_id=report_id,
        user_id=current_user.id,
        org_id=current_user.org_id,
    )
    db.add(audit)


# ── PDF generation ────────────────────────────────────────────

def _generate_pdf(report) -> bytes:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 2 * cm
    y = height - margin
    line_height = 14

    def new_page():
        nonlocal y
        c.showPage()
        y = height - margin

    def write_line(text, font="Helvetica", size=10, color=colors.black, indent=0):
        nonlocal y
        if y < margin + line_height:
            new_page()
        c.setFont(font, size)
        c.setFillColor(color)
        c.drawString(margin + indent, y, text[:110])
        y -= line_height

    def write_wrapped(text, font="Helvetica", size=10, color=colors.black, indent=0, max_width=None):
        nonlocal y
        if not text:
            return
        effective_width = (max_width or (width - 2 * margin - indent)) / 6
        for line in textwrap.wrap(str(text), width=int(effective_width)):
            write_line(line, font=font, size=size, color=color, indent=indent)

    # Header bar
    c.setFillColor(colors.HexColor("#1e40af"))
    c.rect(0, height - 2.5 * cm, width, 2.5 * cm, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.white)
    c.drawString(margin, height - 1.5 * cm, "Investment Research Report")
    c.setFont("Helvetica", 9)
    c.drawString(margin, height - 2.1 * cm, f"Generated: {report.created_at.strftime('%d %b %Y, %H:%M IST')}")
    y = height - 3 * cm

    result = report.result_data or {}

    # Title
    write_line("", size=4)
    write_wrapped(result.get("title") or report.title, font="Helvetica-Bold", size=13, color=colors.HexColor("#111827"))
    write_line("", size=4)

    # Query
    write_line("Query:", font="Helvetica-Bold", size=9, color=colors.HexColor("#6b7280"))
    write_wrapped(report.query, font="Helvetica-Oblique", size=9, color=colors.HexColor("#374151"), indent=10)
    y -= 4

    # Summary
    summary = result.get("summary")
    if summary:
        write_line("Executive Summary", font="Helvetica-Bold", size=11, color=colors.HexColor("#1e40af"))
        y -= 2
        write_wrapped(summary, size=10, color=colors.HexColor("#374151"))
        y -= 6

    # Companies
    companies = result.get("companies_analyzed", [])
    if companies:
        write_line("Companies Analysed: " + ", ".join(companies), font="Helvetica-Bold", size=9, color=colors.HexColor("#6b7280"))
        y -= 4

    # Sections
    for section in result.get("sections", []):
        title = section.get("title", "")
        content = section.get("content", "")
        if not title and not content:
            continue
        y -= 4
        c.setStrokeColor(colors.HexColor("#e5e7eb"))
        c.line(margin, y, width - margin, y)
        y -= 8
        write_line(title, font="Helvetica-Bold", size=11, color=colors.HexColor("#111827"))
        y -= 2
        if content:
            write_wrapped(content, size=10, color=colors.HexColor("#374151"))
        y -= 4

    # Sources
    sources = result.get("sources") or report.sources or []
    if sources:
        y -= 4
        c.setStrokeColor(colors.HexColor("#e5e7eb"))
        c.line(margin, y, width - margin, y)
        y -= 8
        write_line("Sources", font="Helvetica-Bold", size=11, color=colors.HexColor("#111827"))
        y -= 2
        for src in sources:
            if isinstance(src, dict):
                label = f"• {src.get('source', '')} — {src.get('detail', '')}"
            else:
                label = f"• {src}"
            write_line(label, size=9, color=colors.HexColor("#6b7280"), indent=8)

    # Footer
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#9ca3af"))
    c.drawString(margin, 1 * cm, "Klypup Investment Research Dashboard  |  For internal use only")

    c.save()
    return buffer.getvalue()
