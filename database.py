"""Conexión a la base de datos."""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config import get_settings


class Base(DeclarativeBase):
    pass


_database_url = get_settings().database_url
_connect_args = {"check_same_thread": False} if _database_url.startswith("sqlite") else {}
engine = create_engine(_database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

# Una sola sesión para todo el servicio: se abre al arrancar y se reutiliza.
sesion = SessionLocal()
