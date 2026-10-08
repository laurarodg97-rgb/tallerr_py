"""Conexion SQLAlchemy y ciclo de vida de sesiones por peticion."""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings


class Base(DeclarativeBase):
    """Base declarativa compartida por los modelos del servicio."""


_database_url = get_settings().database_url
_connect_args = {"check_same_thread": False} if _database_url.startswith("sqlite") else {}
engine = create_engine(_database_url, connect_args=_connect_args)

if _database_url.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _activar_claves_foraneas(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Abre una sesion para la peticion y la cierra al terminar."""

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
