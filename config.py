"""Configuracion del servicio desde variables de entorno y ``.env``."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Valores de configuracion con defaults seguros para desarrollo local."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite:///app.db"
    secreto_firma: str = "secreto-local-de-ejemplo"
    clave_api_reaseguro: str = "clave-local-de-ejemplo"
    ruta_modelo: str = "modelo.pkl"
    umbral_alto_riesgo: float = 0.6


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Entrega una instancia por proceso para no releer ``.env`` en cada ruta."""

    return Settings()
