"""
FastAPI Application

Main application entry point.
"""

from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import session
from starlette.responses import JSONResponse

from app.api.routes import persons_router, tenants_router
from app.core.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="EAP Platform API",
)

# Include routers
app.include_router(tenants_router)
app.include_router(persons_router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    try:  
        await session.execute(text("SELECT 1"))  
        return {"status": "ready", "database": "connected"}  
    except Exception as e:  
        return JSONResponse(  
            status_code=503,  
            content={"status": "not ready", "database": "disconnected"}  
        ) 