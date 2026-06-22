from pydantic import BaseModel, Field
from datetime import datetime 

class OrgResponse(BaseModel):
    id : str
    name : str
    slug : str
    description : str | None= None
    invite_code : str
    created_at : datetime

    model_config= {"from_attributes": True}


class OrgUpdateRequest(BaseModel):
    name: str | None = Field(default=None , max_length=255)
    description: str| None = Field(default=None, max_length=1000)

class OrgMemberResponse(BaseModel):
    id : str
    email : str
    full_name : str
    role : str
    created_at : datetime

    model_config= {"from_attributes": True}

