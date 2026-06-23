"""
Seed script: Populates the database with demo data for evaluation.

Creates 2 Organization with sepeate users to demo multi-tenant isolation .
  - Org A: "Alpha Capital Research" → admin@alpha.com (Admin), analyst@alpha.com (Analyst)
  - Org B: "Beta Ventures" → admin@beta.com (Admin)

All Passwords : password123

Run : python -m scripts.seed


"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, AsyncSessionLocal, Base
from app.models import Organization, User, UserRole, ResearchReport, WatchlistItem
from app.utils.security import hash_password


async def seed():

    async with engine.begin() as conn:  #Connection (conn) is a low-level database connection used for executing SQL and schema-related operations such as create_all() and drop_all().
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:   # Session (session) is a higher-level ORM object used to manage model instances and transactions. It tracks Python objects and converts operations like add(), update(), and delete() into SQL statements.
        # ── Organization A ==========
        org_a = Organization(
            name="Alpha Capital Research",
            slug="alpha-capital",
            description="Equity research and investment analysis firm",
            invite_code="alpha123",
        )
        session.add(org_a)
        await session.flush()

        admin_a = User(
            email="admin@alpha.com",
            full_name="Priya Sharma",
            hashed_password=hash_password("password123"),
            role=UserRole.ADMIN,
            org_id=org_a.id,
        )
        analyst_a = User(
            email="analyst@alpha.com",
            full_name="Rahul Mehta",
            hashed_password=hash_password("password123"),
            role=UserRole.ANALYST,
            org_id=org_a.id,
        )
        session.add_all([admin_a, analyst_a])
        await session.flush()

        # Sample research reports for Org A
        reports_a = [
            ResearchReport(
                title="Reliance Industries Q3 FY25 Earnings Analysis",
                query="Analyse Reliance Industries Q3 FY25 earnings. Compare revenue growth across Jio, Retail, and O2C segments.",
                result_data={
                    "summary": "Reliance Industries reported consolidated revenue of ₹2.43 lakh crore in Q3 FY25, with Jio Platforms leading growth at 18% YoY...",
                    "companies": ["RELIANCE.NS"],
                    "sections": ["earnings", "segment_breakdown", "outlook"],
                },
                sources=[
                    {"source": "Yahoo Finance", "type": "market_data", "url": "https://finance.yahoo.com"},
                    {"source": "BSE Filing - Quarterly Results", "type": "document", "url": "https://bseindia.com"},
                ],
                tags=["Q3 FY25", "Conglomerate", "Earnings Analysis"],
                status="completed",
                org_id=org_a.id,
                created_by=analyst_a.id,
            ),
            ResearchReport(
                title="TCS vs Infosys — IT Sector Comparison FY25",
                query="Compare TCS and Infosys on revenue growth, margins, deal wins, and valuation for FY25.",
                result_data={
                    "summary": "TCS maintains its lead with stronger deal wins at $10.2B while Infosys upgrades guidance to 4.5–5% CC growth...",
                    "companies": ["TCS.NS", "INFY.NS"],
                    "sections": ["comparison", "deal_wins", "valuation", "risks"],
                },
                sources=[
                    {"source": "Yahoo Finance", "type": "market_data", "url": "https://finance.yahoo.com"},
                    {"source": "NSE Filing - Quarterly Results", "type": "document", "url": "https://nseindia.com"},
                ],
                tags=["IT Sector", "Peer Comparison", "FY25"],
                status="completed",
                org_id=org_a.id,
                created_by=analyst_a.id,
            ),
        ]
        session.add_all(reports_a)

        # Watchlist items for Org A
        watchlist_a = [
            WatchlistItem(symbol="RELIANCE.NS", company_name="Reliance Industries Ltd", notes="Jio + Retail growth story", org_id=org_a.id, added_by=analyst_a.id),
            WatchlistItem(symbol="TCS.NS", company_name="Tata Consultancy Services", notes="Strong deal pipeline, premium valuation", org_id=org_a.id, added_by=analyst_a.id),
            WatchlistItem(symbol="HDFCBANK.NS", company_name="HDFC Bank Ltd", notes="Post-merger NIM normalisation watch", org_id=org_a.id, added_by=admin_a.id),
            WatchlistItem(symbol="INFY.NS", company_name="Infosys Ltd", notes="Guidance upgrade potential", org_id=org_a.id, added_by=analyst_a.id),
        ]
        session.add_all(watchlist_a)

        # ── Organization B ────────────────────────────────────
        org_b = Organization(
            name="Beta Ventures",
            slug="beta-ventures",
            description="Early-stage venture capital fund",
            invite_code="beta456",
        )
        session.add(org_b)
        await session.flush()

        admin_b = User(
            email="admin@beta.com",
            full_name="Ananya Gupta",
            hashed_password=hash_password("password123"),
            role=UserRole.ADMIN,
            org_id=org_b.id,
        )
        session.add(admin_b)
        await session.flush()

        # Sample report for Org B (different from Org A — proves isolation)
        report_b = ResearchReport(
            title="Indian Banking Sector — HDFC Bank vs ICICI Bank",
            query="Compare HDFC Bank and ICICI Bank on NIM, asset quality, loan growth, and capital adequacy ratios.",
            result_data={
                "summary": "HDFC Bank leads in absolute profitability while ICICI Bank shows faster loan growth and improving return on assets...",
                "companies": ["HDFCBANK.NS", "ICICIBANK.NS"],
                "sections": ["balance_sheet", "asset_quality", "capital_adequacy", "comparison"],
            },
            sources=[
                {"source": "Yahoo Finance", "type": "market_data", "url": "https://finance.yahoo.com"},
                {"source": "RBI — Quarterly Banking Statistics", "type": "document", "url": "https://rbi.org.in"},
            ],
            tags=["Banking", "Peer Comparison", "NIM Analysis"],
            status="completed",
            org_id=org_b.id,
            created_by=admin_b.id,
        )
        session.add(report_b)

        watchlist_b = [
            WatchlistItem(symbol="HDFCBANK.NS", company_name="HDFC Bank Ltd", notes="Deposit growth vs credit growth watch", org_id=org_b.id, added_by=admin_b.id),
            WatchlistItem(symbol="ICICIBANK.NS", company_name="ICICI Bank Ltd", notes="ROA improvement trajectory", org_id=org_b.id, added_by=admin_b.id),
            WatchlistItem(symbol="KOTAKBANK.NS", company_name="Kotak Mahindra Bank Ltd", notes="Mgmt transition and digital banking", org_id=org_b.id, added_by=admin_b.id),
        ]
        session.add_all(watchlist_b)

        await session.commit()

        print("✅ Seed data created successfully!")
        print()
        print("Demo Accounts:")
        print("─" * 50)
        print("Org A: Alpha Capital Research")
        print("  Admin:   admin@alpha.com   / password123")
        print("  Analyst: analyst@alpha.com  / password123")
        print()
        print("Org B: Beta Ventures")
        print("  Admin:   admin@beta.com    / password123")
        print()
        print("Invite Codes:")
        print(f"  Alpha Capital: alpha123")
        print(f"  Beta Ventures: beta456")



if __name__ == "__main__":
    asyncio.run(seed())