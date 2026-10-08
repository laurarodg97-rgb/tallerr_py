"""
polizas-api-v0 — Gestión de pólizas y siniestros.
Aseguradora Santo Tomás · prototipo interno.
"""
import hashlib
import pickle
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from config import Settings, get_settings
from database import get_db
from esquemas import (
    PolizaActualizacion,
    PolizaEntrada,
    PolizaSalida,
    PrediccionSalida,
    PuntuacionEntrada,
    PuntuacionSalida,
    ResumenPolizaSalida,
    HealthSalida,
    SiniestroEntrada,
    SiniestroSalida,
)
from modelos import Poliza, Prediccion, Siniestro

with open(get_settings().ruta_modelo, "rb") as fh:
    modelo = pickle.load(fh)

app = FastAPI(title="Pólizas API", version="0.1.0")


def firmar(numero: str, settings: Settings) -> str:
    return hashlib.sha256(f"{numero}:{settings.secreto_firma}".encode()).hexdigest()


def _siniestro(s: Siniestro) -> dict:
    return {"id": s.id, "poliza_id": s.poliza_id, "numero_poliza": s.poliza.numero,
            "fecha": s.fecha, "monto": s.monto, "descripcion": s.descripcion, "estado": s.estado}


def _poliza(p: Poliza) -> dict:
    return {
        "id": p.id, "numero": p.numero, "asegurado": p.asegurado, "tipo": p.tipo,
        "prima": p.prima, "fecha_inicio": p.fecha_inicio, "fecha_fin": p.fecha_fin,
        "siniestros": [{"id": s.id, "fecha": s.fecha, "monto": s.monto,
                        "descripcion": s.descripcion, "estado": s.estado} for s in p.siniestros],
    }


@app.get("/health", response_model=HealthSalida)
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """Comprueba que el proceso responde y que la base acepta una consulta."""

    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        db.rollback()
        return {"estado": "degradado", "base_datos": "error"}
    return {"estado": "ok", "base_datos": "ok"}


@app.post("/polizas", response_model=PolizaSalida, status_code=status.HTTP_201_CREATED)
def crear_poliza(
    datos: PolizaEntrada,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    poliza = Poliza(numero=datos.numero, asegurado=datos.asegurado, tipo=datos.tipo,
                    prima=datos.prima, fecha_inicio=datos.fecha_inicio, fecha_fin=datos.fecha_fin,
                    token_firma=firmar(datos.numero, settings))
    for s in datos.siniestros:
        poliza.siniestros.append(Siniestro(
            fecha=s.fecha,
            monto=s.monto,
            descripcion=s.descripcion,
            estado=s.estado,
        ))
    db.add(poliza)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe una póliza con ese número.",
        ) from exc
    db.refresh(poliza)
    return _poliza(poliza)


@app.get("/polizas", response_model=list[PolizaSalida])
def listar_polizas(db: Session = Depends(get_db)):
    return [_poliza(p) for p in db.scalars(select(Poliza).order_by(Poliza.id))]


@app.get("/polizas/{id_poliza}", response_model=PolizaSalida)
def obtener_poliza(id_poliza: int, db: Session = Depends(get_db)):
    poliza = db.get(Poliza, id_poliza)
    if poliza is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Póliza no encontrada.")
    return _poliza(poliza)


@app.put("/polizas/{id_poliza}", response_model=PolizaSalida)
def actualizar_poliza(id_poliza: int, datos: PolizaActualizacion, db: Session = Depends(get_db)):
    poliza = db.get(Poliza, id_poliza)
    if poliza is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Póliza no encontrada.")
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(poliza, campo, valor)
    db.commit()
    db.refresh(poliza)
    return _poliza(poliza)


@app.post(
    "/polizas/{id_poliza}/siniestros",
    response_model=SiniestroSalida,
    status_code=status.HTTP_201_CREATED,
)
def declarar_siniestro(id_poliza: int, datos: SiniestroEntrada, db: Session = Depends(get_db)):
    poliza = db.get(Poliza, id_poliza)
    if poliza is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Póliza no encontrada.")
    siniestro = Siniestro(poliza_id=id_poliza, fecha=datos.fecha, monto=datos.monto,
                          descripcion=datos.descripcion, estado=datos.estado)
    db.add(siniestro)
    db.commit()
    db.refresh(siniestro)
    return {"id": siniestro.id, "poliza_id": siniestro.poliza_id, "numero_poliza": poliza.numero,
            "fecha": siniestro.fecha,
            "monto": siniestro.monto, "descripcion": siniestro.descripcion, "estado": siniestro.estado}


@app.get("/siniestros", response_model=list[SiniestroSalida])
def listar_siniestros(db: Session = Depends(get_db)):
    return [_siniestro(s) for s in db.scalars(select(Siniestro).order_by(Siniestro.id))]


@app.get("/resumen", response_model=list[ResumenPolizaSalida])
def resumen(db: Session = Depends(get_db)):
    filas = []
    for p in db.scalars(select(Poliza).order_by(Poliza.id)):
        filas.append({"numero": p.numero, "n_siniestros": len(p.siniestros),
                      "monto_total": round(sum(s.monto for s in p.siniestros), 2)})
    return filas


@app.post("/score", response_model=PuntuacionSalida)
def puntuar(
    datos: PuntuacionEntrada,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    poliza = db.scalar(select(Poliza).where(Poliza.numero == datos.numero))
    if poliza is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Póliza no encontrada.")
    rasgos = [[poliza.prima, len(poliza.siniestros), sum(s.monto for s in poliza.siniestros),
               (date.today() - poliza.fecha_inicio).days]]
    puntaje = float(modelo.predict_proba(rasgos)[0][1])
    prediccion = Prediccion(poliza_id=poliza.id, puntaje=puntaje,
                            alto_riesgo=puntaje > settings.umbral_alto_riesgo)
    db.add(prediccion)
    db.commit()
    return {"numero": poliza.numero, "puntaje": round(puntaje, 4),
            "alto_riesgo": prediccion.alto_riesgo}


@app.get("/predicciones", response_model=list[PrediccionSalida])
def listar_predicciones(db: Session = Depends(get_db)):
    return [{"id": pr.id, "poliza_id": pr.poliza_id, "numero": pr.poliza.numero,
             "puntaje": pr.puntaje, "alto_riesgo": pr.alto_riesgo, "creado_en": pr.creado_en}
            for pr in db.scalars(select(Prediccion).order_by(Prediccion.id))]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
