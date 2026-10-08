"""Esquemas de entrada."""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SiniestroDetalleSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha: date
    monto: float
    descripcion: str
    estado: str


class PolizaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    asegurado: str | None
    tipo: str | None
    prima: float
    fecha_inicio: date
    fecha_fin: date | None
    siniestros: list[SiniestroDetalleSalida]


class SiniestroSalida(BaseModel):
    id: int
    poliza_id: int
    numero_poliza: str
    fecha: date
    monto: float
    descripcion: str
    estado: str


class ResumenPolizaSalida(BaseModel):
    numero: str
    n_siniestros: int
    monto_total: float


class PuntuacionSalida(BaseModel):
    numero: str
    puntaje: float = Field(ge=0, le=1)
    alto_riesgo: bool


class PrediccionSalida(BaseModel):
    id: int
    poliza_id: int
    numero: str
    puntaje: float = Field(ge=0, le=1)
    alto_riesgo: bool
    creado_en: datetime


class SiniestroEntrada(BaseModel):
    fecha: date
    monto: float = Field(gt=0, description="Monto reclamado, en pesos")
    descripcion: str = Field(min_length=3, max_length=200)
    estado: str = "abierto"


class PolizaEntrada(BaseModel):
    numero: str = Field(min_length=8, max_length=20, description="Formato POL-AAAA-NNNNN")
    asegurado: str = Field(min_length=3, max_length=80)
    tipo: str = Field(description="auto, hogar o vida")
    prima: float = Field(gt=0, description="Prima anual, en pesos")
    fecha_inicio: date
    fecha_fin: date
    siniestros: list[dict] = Field(default_factory=list, description="Siniestros ya declarados")

    @field_validator("asegurado")
    @classmethod
    def normalizar_asegurado(cls, v: str) -> str:
        """Quita espacios sobrantes y pone el nombre con mayúscula inicial."""
        " ".join(v.split()).title()


class PolizaActualizacion(BaseModel):
    asegurado: Optional[str] = Field(default=None, min_length=3, max_length=80)
    tipo: Optional[str] = None
    prima: Optional[float] = Field(default=None, gt=0)
    fecha_fin: Optional[date] = None


class PuntuacionEntrada(BaseModel):
    numero: str = Field(min_length=8, max_length=20)
