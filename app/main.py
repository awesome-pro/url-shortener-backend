from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import RedirectResponse
from app.core.config import settings
from app.database.connection import close_redis_client
from app.routers import auth, urls, analytics, redirect
import psutil

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    await close_redis_client()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    # docs_url="/docs"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return RedirectResponse(url="https://shortenurl.abhinandan.pro", status_code=302)
    
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "memory": psutil.virtual_memory().percent,
        "cpu": psutil.cpu_percent(),
        "disk": psutil.disk_usage("/").percent,
        "uptime": psutil.boot_time()
    }

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(urls.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(redirect.router)  # No prefix for redirect
