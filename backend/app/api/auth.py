import re
from fastapi import APIRouter , Depends , HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Organization , User , UserRole
from app.schemas.user import SignupRequest , LoginRequest , AuthResponse, UserResponse, TokenResponse
from app.utils.security import hash_password , verify_password , create_access_token
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

def _slugify(name: str)->str:   
    """Convert org name to URL-safe slug."""
    slug= re.sub(r"[^\w\s-]", "" , name.lower().strip())    # re.sub(pattern, replacement, text)
    return re.sub(r"[\s_]", "-", slug)

@router.post("/signup", response_model = AuthResponse, status_code= status.HTTP_201_CREATED)
async def signup(payload: SignupRequest, db: AsyncSession = Depends(get_db)):
        """Registeer a new user .

        Two flows :
        1. Provide org_name -> creates a new org, user becomes Admin
        2. Provide invite_code -> joins existing org as Analyst
        """

        # Check if email already taken 
        existing = await db.execute(select(User).where(User.email == payload.email))
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code = status.HTTP_409_CONFLICT,
                detail= "Email already Registered"
            )

        # Must provide either org_name or invite_code 
        if not payload.org_name and not payload.invite_code:
            raise HTTPException(
                status_code = status.HTTP_400_BAD_REQUEST, 
                detail= "Provide either org_name (Creating new as admin) or invite_code(Join as Analyst)"

            )
        if payload.org_name:
            # Flow 1: Creating new organization and person as ADMIN
            slug = _slugify(payload.org_name)

            # Checking slug Uniqueness
            existing_org = await db.execute(
                select(Organization).where(slug== Organization.slug)
            )

            if existing_org.scalar_one_or_none():   # None - > return False so  condition will not execute
                raise HTTPException(
                    status_code = status.HTTP_409_CONFLICT,
                    detail= "Organization name already taken"
                )

            org = Organization(name = payload.org_name, slug= slug) 
            db.add(org)    # Adding obj object in database session , still in memory 

            await db.flush() # Inserting the query into database so to get org.id before creating user
            role = UserRole.ADMIN
        else:

            # Flow 2: Join Existing organization via invite code as analyst
            result = await db.execute(
                select(Organization).where(Organization.invite_code== payload.invite_code)         
            )

            org = result.scalar_one_or_none()
            if not org:
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid invite code",
                )

            role= UserRole.ANALYST

        # Create  user
        user = User(
            email= payload.email,
            full_name = payload.full_name,
            hashed_password= hash_password(payload.password),
            role= role , 
            org_id = org.id,
        )

        db.add(user)
        await db.flush()

        # Generate JWT

        token = create_access_token(data={"sub": user.id, "org_id": org.id, "role": role.value})

        return AuthResponse(
            user= UserResponse(
                id= user.id,
                email= user.email,
                full_name = user.full_name , 
                role = user.role , 
                org_id = user.org_id, 
                org_name = org.name , 
                is_active = user.is_active , 
                created_at = user.created_at,
            ),
            token = TokenResponse(access_token= token),
        )

                

@router.post("/login" , response_model = AuthResponse)
async def login(payload: LoginRequest , db: AsyncSession = Depends(get_db)):
    """Authenticating User and return JWT token """

    result = await db.execute(select(User).where(User.email== payload.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    # Fetch org name
    org_result = await db.execute(
        select(Organization).where(Organization.id == user.org_id)
    )
    org = org_result.scalar_one()

    token = create_access_token(
        data={"sub": user.id, "org_id": user.org_id, "role": user.role.value}
    )


    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            org_id=user.org_id,
            org_name=org.name,
            is_active=user.is_active,
            created_at=user.created_at,
        ),
        token=TokenResponse(access_token=token),
    )

@router.get("/me", response_model = UserResponse)
async def get_me(
        current_user : User = Depends(get_current_user),
        db : AsyncSession = Depends(get_db), ):

        """
        Get Current authenticated user's profile
        """

        org_result= await db.execute(
            select(Organization).where(Organization.id == current_user.org_id)
        )

        org = org_result.scalar_one()  # Extract exactly one result else Exception

        return UserResponse(
            id= current_user.id,
            email= current_user.email, 
            full_name = current_user.full_name, 
            role= current_user.role,
            org_id= current_user.org_id,
            org_name = org.name,
            is_active= current_user.is_active, 
            created_at= current_user.created_at, 

        )




