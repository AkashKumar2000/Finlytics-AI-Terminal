from pydantic import BaseModel , EmailStr , Field 
from datetime import datetime
from app.models.user import UserRole

#--------------Auth Request Schemas---------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8 , max_length=128)
    full_name : str = Field(min_length=1, max_length=255)
    org_name : str | None = Field(
        default=None ,
        description="Create a new org. If omitted , must provide inivite_code.",
    )
    invite_code : str | None = Field(
        default= None,
        description="Join an existing org. If omitted, must provide org_name. ",
    )


class LoginRequest(BaseModel):
    email: EmailStr
    password: str



#----------------------------------------
# AUTH RESPONSE SCHEMAS
#------------------------------------------

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id : str
    email: str
    full_name : str
    role : UserRole
    org_id : str
    org_name : str | None= None
    is_active : bool
    created_at : datetime

    model_config = {"from_attributes": True}

class AuthResponse(BaseModel):
    user: UserResponse
    token : TokenResponse