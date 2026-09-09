from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    validate_configuration,
)

from app.db.database import (
    initialize_database,
)

from app.routers.analysis import (
    router as analysis_router,
)

from app.routers.analyses import (
    router as analyses_router,
)

from app.routers.decisions import (
    router as decisions_router,
)


# ============================================================
# CONFIGURATION
# ============================================================

validate_configuration()


# ============================================================
# DATABASE
# ============================================================

initialize_database()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(

    title="Greenlight Scout API",

    description=(
        "Evidence-first agentic "
        "pre-production intelligence API."
    ),

    version="0.3.0",
)


# ============================================================
# CORS
# ============================================================

allowed_origins = [

    "http://localhost:5173",

    "http://127.0.0.1:5173",
]


app.add_middleware(

    CORSMiddleware,

    allow_origins=
        allowed_origins,

    allow_credentials=
        False,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(
    analysis_router
)

app.include_router(
    analyses_router
)

app.include_router(
    decisions_router
)


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/health",
    tags=[
        "System"
    ],
)
async def health():

    return {

        "status":
            "healthy",

        "service":
            "greenlight-scout-api",

        "version":
            "0.3.0",

        "database":
            "configured",

        "persistence":
            "sqlalchemy",
    }


# ============================================================
# ROOT
# ============================================================

@app.get(
    "/",
    tags=[
        "System"
    ],
)
async def root():

    return {

        "name":
            "Greenlight Scout",

        "message":
            (
                "Agentic pre-production "
                "intelligence backend."
            ),

        "docs":
            "/docs",
    }