import os
from pathlib import Path

from dotenv import load_dotenv


# ============================================================
# PROJECT PATHS
# ============================================================

BACKEND_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

DATA_DIR = (
    BACKEND_DIR
    / "data"
)

DATA_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LOAD BACKEND .ENV
# ============================================================

ENV_FILE = (
    BACKEND_DIR
    / ".env"
)

load_dotenv(
    dotenv_path=ENV_FILE
)


# ============================================================
# GOOGLE CLOUD
# ============================================================

PROJECT_ID = os.getenv(
    "GOOGLE_CLOUD_PROJECT",
    "greenlight-scout",
)

LOCATION = os.getenv(
    "GOOGLE_CLOUD_LOCATION",
    "global",
)

MODEL = os.getenv(
    "GREENLIGHT_MODEL",
    "gemini-2.5-flash",
)


# ============================================================
# PARALLEL
# ============================================================

PARALLEL_API_KEY = os.getenv(
    "PARALLEL_API_KEY"
)


# ============================================================
# DATABASE
# ============================================================

DEFAULT_DATABASE_PATH = (
    DATA_DIR
    / "greenlight_scout.db"
)

DEFAULT_DATABASE_URL = (
    "sqlite:///"
    + DEFAULT_DATABASE_PATH
    .as_posix()
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    DEFAULT_DATABASE_URL,
)


# ============================================================
# GOOGLE ENVIRONMENT
# ============================================================

os.environ.setdefault(
    "GOOGLE_CLOUD_PROJECT",
    PROJECT_ID,
)

os.environ.setdefault(
    "GOOGLE_CLOUD_LOCATION",
    LOCATION,
)

os.environ.setdefault(
    "GOOGLE_GENAI_USE_VERTEXAI",
    "True",
)


# ============================================================
# CONFIG VALIDATION
# ============================================================

def validate_configuration() -> None:

    if not PARALLEL_API_KEY:

        raise RuntimeError(
            "PARALLEL_API_KEY is not configured. "
            f"Expected it in: {ENV_FILE}"
        )

    if not DATABASE_URL:

        raise RuntimeError(
            "DATABASE_URL is not configured."
        )