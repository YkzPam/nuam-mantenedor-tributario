# Mantenedor de calificaciones tributarias para NUAM

Proyecto Integrado (TIHI43), Ingeniería en Ciberseguridad, INACAP. Grupo 4: Benjamín Concha, María Jesús Erices y Pablo Doussang. Docente: José Luis Martínez Opazo.

Prototipo académico de la Unidad 3: aplicación web local en Flask para consultar, crear, modificar y desactivar calificaciones tributarias por corredor, cargar archivos CSV con prevalidación, convertir montos a factores con una regla ilustrativa (DEMO-1) y registrar cada operación en una bitácora encadenada con HMAC. SQLite guarda los datos operativos y TinyDB los reportes de carga.

> Demostración con datos ficticios. No es un sistema de NUAM, no usa datos reales y la fórmula, la llave de negocio y los formatos de carga no están aprobados por NUAM.

## Inicio rápido

Requiere Python 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe app.py
```

Abrir `http://127.0.0.1:8765` e ingresar como `operador_a` con la contraseña ficticia `Demo2026!`. Las instrucciones completas para Windows, Linux y macOS, los cuatro usuarios de prueba, Waitress, Docker y la solución de problemas están en [INICIO_UNIDAD3.md](INICIO_UNIDAD3.md).

## Pruebas

```powershell
.\.venv\Scripts\python.exe run_all_tests.py         # 68 casos en cuatro suites
.\.venv\Scripts\python.exe pruebas_estres.py --segundos 60   # 20, 50 y 100 clientes y diez lotes de 1.000 filas
```

Los resultados del 11 de noviembre de 2026 están en [evidencias/](evidencias/LEEME.md).

## Contenido

| Ruta | Descripción |
|---|---|
| `app.py`, `domain.py`, `documentrepo.py`, `schema.sql` | Aplicación, reglas de validación, repositorio documental y esquema SQLite |
| `templates/`, `static/` | Interfaz web |
| `tests/`, `run_all_tests.py`, `pruebas_estres.py` | Pruebas automatizadas y prueba de estrés |
| `ejemplos/` | CSV ficticios para las cargas |
| `wsgi.py`, `Dockerfile` | Ejecución con Waitress; la imagen Docker no se construyó |
| `evidencias/` | Registros de las ejecuciones de la versión 1.1 |
| `docs/` | Documento de asesoría e informe de pruebas de la Unidad 3 |
| `CONTRIBUTING.md`, `CHANGELOG.md` | Flujo de trabajo del equipo e historial de versiones |

`MANIFIESTO_SHA256.json` registra la huella de los archivos del paquete entregado en DreamShaper; este README y la carpeta `docs/` existen solo en el repositorio.

## Pendientes

La prioridad entre datos de la Bolsa y del corredor y el catálogo de instrumentos habilitados dependen de definiciones de NUAM. La usabilidad se evaluó con perfiles simulados y falta repetirla con usuarios reales.
