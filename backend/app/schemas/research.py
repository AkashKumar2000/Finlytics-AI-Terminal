from pydantic import BaseModel , Field
from datetime import datetime

# ---------------------------------------
# RESEARCH REPORT SCHEMAS
#----------======================================


class ResearchQueryRequest(BaseModel):
    """USer Submits a natural language research query"""
    query : str = Field(min_length=5, max_length=2000)

class ResearchReportResponse(BaseModel):
    id: str
    title: str
    query: str
    result_data: dict | None= None
    sources: list | None= None
    tags: list | None= None
    status: str
    created_by : str
    org_id : str
    created_at : datetime
    updated_at : datetime

    model_config = {"from_attributes": True}

class ResearchReportListResponse(BaseModel):
    id : str
    title : str
    query : str
    tags : list | None= None
    status : str
    created_at : datetime

    model_config = {"from_attributes": True}


class ResearchUpdateRequest(BaseModel):
    title: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None

#================================================
# WATCHLIST SCHEMAS
#==============================================================

class WatchlistAddRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=20)
    company_name: str = Field(min_length=1, max_length=255)
    notes: str | None = None


class WatchlistResponse(BaseModel):
    id: str
    symbol: str
    company_name: str
    notes: str | None = None
    org_id: str
    added_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


