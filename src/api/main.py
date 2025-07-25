from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from ..database import create_tables
from .endpoints import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    create_tables()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Reform UK Messaging Analysis API",
    description="""
    ## Reform UK Digital Footprint Analysis API
    
    This API enables submission and analysis of political messaging data from Reform UK's digital platforms.
    
    ### Features
    - **Message Processing**: Submit individual or bulk political messages for analysis
    - **Constituency Analysis**: Access UK constituency data and candidate information
    - **Candidate Tracking**: Monitor individual candidate messaging across platforms
    - **Keyword Extraction**: Automatic NLP-based keyword and theme extraction
    - **Geographic Analysis**: Messages categorized by geographic scope (national, regional, local)
    
    ### Data Sources Supported
    - Twitter/X posts
    - Facebook posts
    - Website articles
    - Meta Ad Library advertisements
    
    ### Phase 2 Features
    - Constituency-level analysis across UK regions
    - Individual candidate message tracking
    - Social media account linking
    - Geographic message distribution
    """,
    version="2.0.0",
    lifespan=lifespan,
    contact={
        "name": "Campaign Labs",
        "url": "https://github.com/your-org/party-digital-footprint",
    },
    license_info={
        "name": "MIT License",
    }
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include message endpoints
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Reform UK Messaging Analysis API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred",
            "details": {"error": str(exc)}
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)