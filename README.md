# Mantenedor de calificaciones tributarias NUAM

Proyecto Integrado (TIHI43) de Ingeniería en Ciberseguridad, INACAP. Grupo 4: Benjamín Concha, María Jesús Erices y Pablo Doussang. Docente: José Luis Martínez Opazo.

El prototipo de la Unidad 3 es una aplicación web local en Flask para consultar, crear, modificar y desactivar calificaciones tributarias por corredor, cargar archivos CSV con prevalidación, convertir montos a factores con una regla ilustrativa (DEMO-1) y registrar cada operación en una bitácora encadenada con HMAC. SQLite guarda los datos operativos y TinyDB los reportes de carga.

> Demostración académica con datos ficticios. No es un sistema de NUAM ni se conecta con sus servicios. La fórmula, la llave de negocio y los formatos de carga no están aprobados por NUAM.

## 1. Preparación del entorno

Se requiere Windows 10 u 11 y Python 3.12 instalado desde [python.org](https://www.python.org/downloads/), con la casilla **Add python.exe to PATH** marcada. La primera preparación necesita internet para descargar las dependencias fijadas en `requirements-lock.txt`.

1. Descargar el proyecto con **Code → Download ZIP** y extraerlo en una carpeta con permisos de escritura, por ejemplo `C:\NUAM`. No se debe ejecutar desde dentro del ZIP.
2. Hacer doble clic en `preparar.cmd`. Crea el entorno `.venv` dentro de la carpeta e instala las dependencias.

En Linux o macOS, y para la instalación manual en PowerShell, los pasos están en [INICIO_UNIDAD3.md](INICIO_UNIDAD3.md).

## 2. Ejecución

Hacer doble clic en `iniciar.cmd` y abrir <http://127.0.0.1:8765> en el mismo equipo. La ventana debe quedar abierta mientras se usa la demostración; se detiene con `Ctrl+C`. Si falta el entorno, `iniciar.cmd` ejecuta antes `preparar.cmd`.

En el primer arranque se crea la carpeta `data/` con la base SQLite, una clave local aleatoria, los archivos privados y el registro operativo. Esa carpeta no se sube al repositorio ni se comparte. Para partir de cero se detiene el servidor y se borra `data/`.

## 3. Usuarios ficticios

Todas las cuentas usan la contraseña ficticia `Demo2026!`.

| Usuario | Perfil | Corredores | Puede |
| --- | --- | --- | --- |
| `operador_a` | Operador | DEMO-A | Consultar, crear, modificar, desactivar y cargar en su corredor |
| `operador_b` | Operador | DEMO-B | Lo mismo, solo en DEMO-B |
| `supervisor` | Supervisor | DEMO-A y DEMO-B | Mantener ambos corredores y revisar su bitácora |
| `admin` | Administrador | Ninguno | Gestionar perfiles y asignaciones; no ve calificaciones |

## 4. Pruebas

Hacer doble clic en `verificar.cmd`. Ejecuta las cuatro suites (68 casos) con bases temporales y deja el informe en `evidencias/`. GitHub Actions repite las mismas suites en Windows y Ubuntu en cada cambio del repositorio.

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
| `tests/`, `run_all_tests.py` | Cuatro suites automatizadas |
| `pruebas_estres.py` | Carga sostenida de 20, 50 y 100 clientes y lotes de 1.000 filas |
| `ejemplos/` | Cinco CSV ficticios: dos válidos y tres con errores |
| `wsgi.py`, `requirements-servidor.txt`, `Dockerfile` | Ejecución opcional con Waitress; la imagen Docker no se construyó |
| `preparar.cmd`, `iniciar.cmd`, `verificar.cmd` | Accesos para Windows |
| `evidencias/` | Informes de las ejecuciones de la versión 1.1 |
| `docs/` | Documentación técnica numerada y documentos entregados |
| `CONTRIBUTING.md`, `CHANGELOG.md` | Flujo de trabajo del equipo e historial de versiones |
| `MANIFIESTO_SHA256.json` | Huella de cada archivo del paquete entregado en DreamShaper |

## 6. Documentación

1. [Arquitectura y datos](docs/01-arquitectura-y-datos.md)
2. [Seguridad del código](docs/02-seguridad.md)
3. [Pruebas y resultados](docs/03-pruebas-y-resultados.md)
4. [Correspondencia con la rúbrica](docs/04-rubrica.md)
5. [Verificación del paquete](docs/05-verificacion.md)

Los documentos de la entrega están en `docs/`: la propuesta de asesoría (`Propuesta_asesoria_NUAM_Grupo4.docx`) y el informe de pruebas extendido (`Informe_pruebas_NUAM_Grupo4_extendido.docx`).

## 7. Alcance y pendientes

La prioridad entre datos de la Bolsa y del corredor y el catálogo de instrumentos habilitados dependen de definiciones de NUAM. La usabilidad se evaluó con perfiles simulados y falta repetirla con usuarios reales. Los resultados locales no certifican la infraestructura de NUAM, y la validación del docente se confirma por separado.
