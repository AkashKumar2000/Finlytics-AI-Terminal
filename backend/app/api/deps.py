from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


from app.database import get_db
from app.models.user import User, UserRole
from app.utils.security import decode_access_token

security_scheme = HTTPBearer()

async def get_current_user(credentials : HTTPAuthorizationCredentials= Depends(security_scheme), db : AsyncSession = Depends(get_db),)-> User:

    """
    Extract and Validate JWT -> return the authenticated User Object/

    This is the entry point for auth + tenant resolution
    The user's org_id is always available via user.org_id.
    """

    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier",
        )
    
    user_id : str = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user identifier",
        )
    
    result = await db.execute(select(User).where(User.id== user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code = status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
        
    return user 

async def require_admin(current_user : User = Depends(get_current_user))->user:
    """Dependeny that ensure that current user has Admin role"""

    if current_user.role!= UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    return current_user

async def require_analyst(current_user : User = Depends(get_current_user))->User:

    if current_user.role not in (UserRole.ADMIN, UserRole.ANALYST):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Analyst access required",
        )
    return current_user


