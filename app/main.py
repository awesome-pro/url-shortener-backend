from fastapi import FastAPI, Request, Response
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
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
    max_age=86400,  # 24 hours
)

@app.get("/")
def read_root():
    return RedirectResponse(url="https://shortenurl.abhinandan.pro", status_code=302)

# Add explicit OPTIONS handler for all routes
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    """Handle preflight OPTIONS requests"""
    response = Response()
    origin = request.headers.get("origin")
    
    if origin in settings.allowed_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin, Access-Control-Request-Method, Access-Control-Request-Headers"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
    
    return response
    
@app.get(
    "/health",
    summary="System Health Check",
    description="Comprehensive health check endpoint for monitoring system performance and uptime",
    tags=["Health Check"]
)
async def health_check():
    """
    Enhanced health check with performance metrics.
    Used by search engines and monitoring systems to verify service availability.
    """
    health_data = {
        "status": "healthy",
        "service": "ShortURL API",
        "version": settings.app_version,
        "uptime_seconds": psutil.boot_time(),
        "performance": {
            "memory_usage_percent": psutil.virtual_memory().percent,
            "cpu_usage_percent": psutil.cpu_percent(interval=1),
            "disk_usage_percent": psutil.disk_usage("/").percent
        },
    }
    return health_data

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(urls.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(redirect.router)  # No prefix for redirect
