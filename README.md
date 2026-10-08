# Pólizas API

API para registrar pólizas y siniestros, resumir la cartera y puntuar el riesgo
de cada póliza. El servicio usa SQLite por defecto y guarda las predicciones.

## Requisitos

- Python 3.11.9 para ejecución local.
- Docker para ejecutar el contenedor.

## Ejecución local

Desde esta carpeta, cree un entorno e instale las dependencias fijadas:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn main:app --host 127.0.0.1 --port 8000
```

La aplicación y Alembic leen `DATABASE_URL` del entorno o de `.env`. El esquema
se crea con la migración antes de iniciar el servidor.

Compruebe la conexión con `GET http://localhost:8000/health`. La documentación
interactiva está en `http://localhost:8000/docs`.

## Ejecución con Docker

```powershell
docker build -t polizas-api .
docker run --rm -p 8000:8000 polizas-api
```

El contenedor aplica las migraciones al iniciar y escucha en `0.0.0.0:8000`.
El archivo SQLite queda en el sistema de archivos del contenedor: `docker
restart` conserva esos datos; al borrar el contenedor y crear otro, se empieza
con una base vacía.

Para conservar la base al reemplazar el contenedor, monte un volumen y cambie
la URL:

```powershell
docker volume create polizas-datos
docker run --rm -p 8000:8000 -v polizas-datos:/data `
  -e DATABASE_URL=sqlite:////data/app.db polizas-api
```

Puede pasar variables adicionales con `--env-file .env`. No copie `.env` ni una
base de datos local a la imagen.

## Rutas

| Método | Ruta | Función |
|---|---|---|
| POST | `/polizas` | Crea una póliza y sus siniestros iniciales |
| GET | `/polizas` | Lista pólizas con siniestros |
| GET | `/polizas/{id}` | Consulta una póliza |
| PUT | `/polizas/{id}` | Actualiza los campos enviados |
| POST | `/polizas/{id}/siniestros` | Declara un siniestro |
| GET | `/siniestros` | Lista siniestros con su póliza |
| GET | `/resumen` | Resume siniestros y montos por póliza |
| POST | `/score` | Puntúa una póliza y guarda la predicción |
| GET | `/predicciones` | Consulta el histórico de puntuaciones |
| GET | `/health` | Informa el estado de la API y la base de datos |

## Migraciones y pruebas

Para aplicar las migraciones manualmente:

```powershell
alembic upgrade head
```

La batería de contrato se ejecuta con:

```powershell
pytest tests/test_contrato.py
```

`sembrar_datos.py` crea datos sintéticos a través de la API y
`contar_consultas.py` mide las consultas emitidas por los endpoints.
