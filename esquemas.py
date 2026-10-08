"""Esquemas de entrada."""
from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


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
    fecha: date = Field(description="Fecha en que se declaró el siniestro")
    monto: float = Field(gt=0, description="Monto reclamado, en pesos")
    descripcion: str = Field(min_length=3, max_length=200)
    estado: Literal["abierto", "pagado", "rechazado"] = "abierto"


class PolizaEntrada(BaseModel):
    numero: str = Field(min_length=8, max_length=20, description="Formato POL-AAAA-NNNNN")
    asegurado: str = Field(min_length=3, max_length=80)
    tipo: Literal["auto", "hogar", "vida"] = Field(description="Ramo de la póliza")
    prima: float = Field(gt=0, description="Prima anual, en pesos")
    fecha_inicio: date
    fecha_fin: date
    siniestros: list[SiniestroEntrada] = Field(
        default_factory=list,
        description="Siniestros ya declarados",
    )

    @field_validator("numero", mode="before")
    @classmethod
    def normalizar_numero(cls, valor: Any) -> Any:
        """Elimina espacios periféricos del identificador de póliza."""

        return valor.strip() if isinstance(valor, str) else valor

    @field_validator("asegurado", mode="before")
    @classmethod
    def normalizar_asegurado(cls, v: Any) -> Any:
        """Quita espacios sobrantes y pone el nombre con mayúscula inicial."""

        if not isinstance(v, str):
            return v
        return " ".join(v.split()).title()

    @model_validator(mode="after")
    def validar_vigencia(self) -> "PolizaEntrada":
        """La fecha de cierre debe ser posterior al comienzo de vigencia."""

        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("fecha_fin debe ser posterior a fecha_inicio")
        return self


class PolizaActualizacion(BaseModel):
    asegurado: Optional[str] = Field(default=None, min_length=3, max_length=80)
    tipo: Optional[Literal["auto", "hogar", "vida"]] = None
    prima: Optional[float] = Field(default=None, gt=0)
    fecha_fin: Optional[date] = None


class PuntuacionEntrada(BaseModel):
    numero: str = Field(min_length=8, max_length=20)
