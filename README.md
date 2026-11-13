# Mantenedor de calificaciones tributarias NUAM

Proyecto Integrado (TIHI43) de Ingeniería en Ciberseguridad, INACAP. Grupo 4: Benjamín Concha, María Jesús Erices y Pablo Doussang. Docente: José Luis Martínez Opazo.

El prototipo de la Unidad 3 es una aplicación web local en Flask para consultar, crear, modificar y desactivar calificaciones tributarias por corredor, cargar archivos CSV con prevalidación, convertir montos a factores con una regla ilustrativa (DEMO-1) y registrar cada operación en una bitácora encadenada con HMAC. Desde la versión 1.2 controla un catálogo de instrumentos (DEMO-2) y da prioridad a la información de la Bolsa sobre la del corredor (DEMO-3). SQLite guarda los datos operativos y TinyDB los reportes de carga.

> Demostración académica con datos ficticios. No es un sistema de NUAM ni se conecta con sus servicios. La fórmula, la llave de negocio, los formatos de carga y las reglas DEMO-2 y DEMO-3 los definió el equipo y no están aprobados por NUAM.

## 1. Preparación del entorno

Se requiere Windows 10 u 11 y Python 3.12 instalado desde [python.org](https://www.python.org/downloads/), con la casilla **Add python.exe to PATH** marcada. La primera preparación necesita internet para descargar las dependencias fijadas en `requirements-lock.txt`.

1. Descargar el proyecto con **Code → Download ZIP** y extraerlo en una carpeta con permisos de escritura, por ejemplo `C:\NUAM`. No se debe ejecutar desde dentro del ZIP.
2. Hacer doble clic en `preparar.cmd`. Crea el entorno `.venv` dentro de la carpeta e instala las dependencias.

En Linux o macOS, y para la instalación manual en PowerShell, los pasos están en [INICIO_UNIDAD3.md](INICIO_UNIDAD3.md).

## 2. Ejecución

Hacer doble clic en `iniciar.cmd` y abrir <http://127.0.0.1:8765> en el mismo equipo. La ventana debe quedar abierta mientras se usa la demostración; se detiene con `Ctrl+C`. Si falta el entorno, `iniciar.cmd` ejecuta antes `preparar.cmd`.

En el primer arranque se crea la carpeta `data/` con la base SQLite, una clave local aleatoria, los archivos privados y el registro operativo. Esa carpeta no se sube al repositorio ni se comparte. Para partir de cero se detiene el servidor y se borra `data/`. Si `data/` venía de la versión 1.1 o anterior, la versión 1.2 la respalda en `data/respaldo_v1_<fecha>/` y crea una base nueva.

## 3. Usuarios ficticios

Todas las cuentas usan la contraseña ficticia `Demo2026!`.

| Usuario | Perfil | Corredores | Puede |
| --- | --- | --- | --- |
| `operador_a` | Operador | DEMO-A | Consultar, crear, modificar, desactivar y cargar en su corredor; consultar el catálogo |
| `operador_b` | Operador | DEMO-B | Lo mismo, solo en DEMO-B |
| `supervisor` | Supervisor | DEMO-A y DEMO-B | Mantener ambos corredores, cargar archivos de Bolsa, mantener el catálogo y revisar su bitácora |
| `admin` | Administrador | Ninguno | Gestionar perfiles y asignaciones; no ve calificaciones |

## 4. Pruebas

Hacer doble clic en `verificar.cmd`. Ejecuta las cinco suites (88 casos) con bases temporales y deja el informe en `evidencias/`. GitHub Actions repite las mismas suites en Windows, con `verificar.cmd`, y en Ubuntu en cada cambio del repositorio; en la versión 1.2, la [ejecución 24](https://github.com/YkzPam/nuam-mantenedor-tributario/actions/runs/43169732121) aprobó 86 de 86 en ambos.

La prueba de estrés se ejecuta aparte porque dura varios minutos:

```powershell
.\.venv\Scripts\python.exe pruebas_estres.py --segundos 60
```

Los resultados del 11 de noviembre de 2026 y su explicación están en [docs/03-pruebas-y-resultados.md](docs/03-pruebas-y-resultados.md) y en [evidencias/LEEME.md](evidencias/LEEME.md).

## 5. Estructura del proyecto

| Ruta | Contenido |
| --- | --- |
| `app.py`, `domain.py`, `documentrepo.py`, `schema.sql` | Aplicación, validaciones, repositorio documental y esquema SQLite |
| `templates/`, `static/` | Interfaz web |
| `tests/`, `run_all_tests.py` | Cinco suites automatizadas |
| `pruebas_estres.py` | Carga sostenida de 20, 50 y 100 clientes y lotes de 1.000 filas |
| `ejemplos/` | Siete CSV ficticios: dos válidos, tres con errores, uno de Bolsa y uno rechazado por el catálogo |
| `wsgi.py`, `requirements-servidor.txt`, `Dockerfile` | Ejecución opcional con Waitress, directa o en contenedor; la imagen se verificó el 13 de noviembre |
| `preparar.cmd`, `iniciar.cmd`, `verificar.cmd` | Accesos para Windows |
| `evidencias/` | Informes de las ejecuciones de las versiones 1.1 a 1.2 |
| `docs/` | Documentación técnica numerada y documentos entregados |
| `CONTRIBUTING.md`, `CHANGELOG.md` | Flujo de trabajo del equipo e historial de versiones |
| `MANIFIESTO_SHA256.json` | Huella de cada archivo del paquete entregado en DreamShaper (versión 1.2) |

## 6. Documentación

1. [Arquitectura y datos](docs/01-arquitectura-y-datos.md)
2. [Seguridad del código](docs/02-seguridad.md)
3. [Pruebas y resultados](docs/03-pruebas-y-resultados.md)
4. [Correspondencia con la rúbrica](docs/04-rubrica.md)
5. [Verificación del paquete](docs/05-verificacion.md)

Los documentos de la entrega están en `docs/`: la propuesta de asesoría (`Propuesta_asesoria_NUAM_Grupo4.docx`) y el informe de pruebas extendido (`Informe_pruebas_NUAM_Grupo4_extendido.docx`).

## 7. Alcance y pendientes

El catálogo de instrumentos (DEMO-2) y la prioridad de la Bolsa (DEMO-3) son reglas que el equipo definió para la demostración, descritas en [INICIO_UNIDAD3.md](INICIO_UNIDAD3.md#8-reglas-demo-2-y-demo-3); NUAM debe validarlas o reemplazarlas. La usabilidad se evaluó con perfiles simulados y falta repetirla con usuarios reales. Los resultados locales no certifican la infraestructura de NUAM, y la validación del docente se confirma por separado.
