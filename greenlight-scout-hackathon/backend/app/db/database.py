from contextlib import contextmanager

from sqlalchemy import create_engine

from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)

from app.config import (
    DATABASE_URL,
)


# ============================================================
# SQLALCHEMY BASE
# ============================================================

class Base(
    DeclarativeBase
):
    pass


# ============================================================
# ENGINE CONFIGURATION
# ============================================================

engine_options = {
    "pool_pre_ping": True,
}


# SQLite needs this because FastAPI may handle requests
# across different threads.

if DATABASE_URL.startswith(
    "sqlite"
):

    engine_options[
        "connect_args"
    ] = {
        "check_same_thread":
            False
    }


engine = create_engine(
    DATABASE_URL,
    **engine_options,
)


# ============================================================
# SESSION FACTORY
# ============================================================

SessionLocal = sessionmaker(
    bind=engine,

    autoflush=False,

    autocommit=False,

    expire_on_commit=False,

    class_=Session,
)


# ============================================================
# DATABASE SESSION
# ============================================================

@contextmanager
def database_session():

    session = SessionLocal()

    try:

        yield session

        session.commit()

    except Exception:

        session.rollback()

        raise

    finally:

        session.close()


# ============================================================
# INITIALIZATION
# ============================================================

def initialize_database() -> None:

    # Import models here so SQLAlchemy registers
    # their tables before create_all().
    from app.db import models  # noqa: F401

    Base.metadata.create_all(
        bind=engine
    )