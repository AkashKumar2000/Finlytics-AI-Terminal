import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from api.database import init_db
from app.middleware.tenant import TenantMiddleware


# Import routers







#---------------------------------------
# CONFIGURE LOGGING 
#-----------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and Shutdown events"""
    logger.info("Starting Investment Research Terminal")
    await init_db()
    logger.info("Table are successfully created")
    yield # Server return while shutting down
    logger.info("shutting down")


app = FastAPI(
    title= settings.APP_NAME,
    description= "AI powered investment research platform with multi-tenant architecture",
    version= "1.0.0",
    lifespan= lifespan
)

#----------------------------------
# MIDDLEwaRE
#-----------------------------
# oRder matters: CORS first(outermost) , then tenant middleware

app.add_middleware(
    CORSMiddleware,
    allow_origins= settings.CORS_ORIGINS,
    aloow_credentials= True,
    allow_methods=["*"],
    allow_headers=["*"],
)

add.add_middleware(TenantMiddleware)

#------------------------------
# ROUTES
#-------------------------

app.include_router(auth_router, prefix= settings.API_V1_PREFIX)
app.include_router(org_router , prefix= settings.API_V1_PREFIX)
app.include_router(research_router, prefix= settings.API_V1_PREFIX)
app.include_router(watchlist_routers, prefix= settings.API_V1_PREFIX)


# ── Health Check ──────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": settings.APP_NAME}


@app.get("/")
async def root():
    return {
        "message": "Investment Research Dashboard API",
        "docs": "/docs",
        "version": "1.0.0",
    }
