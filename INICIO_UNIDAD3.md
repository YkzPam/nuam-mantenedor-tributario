# Implementación académica del mantenedor tributario NUAM

Proyecto Integrado, Grupo 4 — Unidad 3. Versión 1.1.1 del paquete.

El paquete contiene el prototipo local, sus dependencias fijadas por versión, cinco CSV ficticios, cuatro suites de pruebas y una prueba de estrés sostenida. Al iniciar por primera vez, la aplicación genera una base SQLite con registros ficticios y una clave local. TinyDB conserva los reportes de carga que genera el prototipo. El ZIP no incluye bases existentes, archivos privados, registros ni claves.

## 1. Contenido

| Archivo o carpeta | Uso |
|---|---|
| `app.py` | Aplicación Flask: rutas, permisos, auditoría, cargas y registro operativo |
| `domain.py` | Validaciones, llave provisional y regla ilustrativa DEMO-1 |
| `documentrepo.py` | Reportes de carga en TinyDB |
| `schema.sql` | Diez tablas SQLite con llaves foráneas, restricciones, índices y disparadores |
| `templates/`, `static/` | Interfaz web |
| `wsgi.py` | Punto de entrada para Waitress (opcional) |
| `Dockerfile`, `.dockerignore` | Imagen opcional; redactada, no construida |
| `requirements-lock.txt` | Dependencias de la aplicación con versión exacta |
| `requirements-servidor.txt` | Waitress, solo para la opción de la sección 5 |
| `run_all_tests.py`, `tests/` | 68 casos en cuatro suites |
| `pruebas_estres.py` | Carga sostenida de 20, 50 y 100 clientes y lotes sucesivos de 1.000 filas |
| `ejemplos/` | Cinco CSV ficticios: dos válidos y tres con errores |
| `preparar.cmd`, `iniciar.cmd`, `verificar.cmd` | Accesos para Windows: preparar el entorno, abrir la demostración y ejecutar las pruebas |
| `README.md`, `docs/` | Presentación del proyecto y guías numeradas de arquitectura, seguridad, pruebas, rúbrica y verificación |
| `.github/workflows/verificacion.yml` | Ejecución de las cuatro suites en GitHub Actions con Windows y Ubuntu |
| `CONTRIBUTING.md`, `CHANGELOG.md` | Flujo de trabajo del equipo e historial de versiones |
| `MANIFIESTO_SHA256.json` | Huella SHA-256 de cada archivo |

## 2. Instalación y arranque

Se requiere Python 3.12 y acceso al repositorio de paquetes para instalar las dependencias. Extraer el ZIP en una carpeta con permisos de escritura y abrir la terminal en la raíz extraída, donde está `app.py`.

Windows (PowerShell). No hace falta activar el entorno, por lo que la política de ejecución de scripts no interviene:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe app.py
```

Linux o macOS:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python app.py
```

En Windows, los mismos pasos se ejecutan con doble clic: `preparar.cmd` crea `.venv` e instala las dependencias, `iniciar.cmd` abre la demostración y `verificar.cmd` ejecuta las pruebas.

Si `python --version` no devuelve 3.12, seleccionar la instalación correcta antes de crear el entorno (en Windows, `py -3.12 -m venv .venv`). Abrir `http://127.0.0.1:8765` en el mismo equipo. El servidor se limita al equipo local y se detiene con `Ctrl+C`.

## 3. Usuarios ficticios

Todos usan la contraseña ficticia `Demo2026!`.

| Usuario | Perfil | Corredores | Puede |
|---|---|---|---|
| `operador_a` | Operador | DEMO-A | Consultar, crear, modificar, desactivar y cargar en su corredor |
| `operador_b` | Operador | DEMO-B | Lo mismo, solo en DEMO-B |
| `supervisor` | Supervisor | DEMO-A y DEMO-B | Mantener ambos corredores y revisar su bitácora |
| `admin` | Administrador | Ninguno | Gestionar usuarios y perfiles; no ve calificaciones |

## 4. Recorrido de demostración

Iniciar sesión como `operador_a` y buscar `DEMO-ALFA`. La aplicación permite consultar y mantener calificaciones del corredor asignado, ensayar la conversión de monto a factor y revisar la bitácora. En el módulo de cargas se puede prevalidar `ejemplos/01_montos_valido.csv` y contrastarlo con `ejemplos/03_campos_incompletos.csv`. Para repetir una carga válida ya confirmada se debe usar un ejemplo nuevo con identificadores ficticios distintos o una extracción limpia. Cerrar sesión e ingresar como `operador_b` muestra que DEMO-ALFA no es visible desde otro corredor.

## 5. Servidor WSGI con Waitress (opcional)

`app.py` usa el servidor de desarrollo de Flask. Para una ejecución más cercana a un servidor de aplicaciones, Waitress sirve el mismo código desde `wsgi.py`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-servidor.txt
.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8765 --threads=8 wsgi:app
```

En Linux o macOS: `.venv/bin/waitress-serve --listen=127.0.0.1:8765 --threads=8 wsgi:app`. La variable `NUAM_DATA_DIR` permite dejar la base, la clave y los registros en otra carpeta, por ejemplo una carpeta desechable para la prueba de estrés.

El `Dockerfile` reproduce esos pasos sobre `python:3.12-slim` con un usuario sin privilegios. No se construyó porque el equipo de prueba no tenía el servicio de Docker; si se usa, publicar solo en el equipo local:

```bash
docker build -t nuam-mantenedor:1.1 .
docker run --rm -p 127.0.0.1:8765:8765 -v nuam-datos:/datos nuam-mantenedor:1.1
```

## 6. Pruebas e integridad

```powershell
.\.venv\Scripts\python.exe run_all_tests.py
```

La ejecución utiliza bases temporales y genera su propio informe en `evidencias/`. Los 68 casos cubren dominio, integración, seguridad, rendimiento local, comprobaciones automatizadas de interfaz y la regresión de la versión 1.1.

La prueba de estrés se ejecuta aparte porque dura varios minutos:

```powershell
.\.venv\Scripts\python.exe pruebas_estres.py --segundos 60
```

Sin argumentos usa la aplicación en proceso con una base temporal, 30 segundos por nivel y diez lotes. Con `--url http://127.0.0.1:8765` mide un servidor ya iniciado; en ese caso arrancarlo con `NUAM_DATA_DIR` apuntando a una carpeta desechable, porque la prueba crea registros ficticios. El informe queda en `evidencias/estres_<fecha>/`.

`MANIFIESTO_SHA256.json` identifica el contenido y su huella por archivo. La carpeta `data/` que se crea al arrancar es local y no debe adjuntarse ni compartirse.

## 7. Registro operativo y configuración

Cada solicitud agrega una línea JSON a `data/logs/operacion.log` con fecha, método, ruta declarada (por ejemplo `/api/ratings/<int:rid>`), estado HTTP, duración en milisegundos y perfil. No se registran cuerpos, parámetros de búsqueda, cookies, tokens ni contraseñas. Al superar 5 MB el archivo rota a `operacion.log.1` y se conservan hasta tres archivos anteriores. La bitácora de negocio con cadena HMAC sigue en la base SQLite.

`NUAM_ROLES_FACTOR_MANUAL` define qué perfiles ingresan factores manualmente, sea en el formulario o en cargas `factores-DEMO`. Sin la variable rige la matriz de la Unidad 2 (operador y supervisor). Con `NUAM_ROLES_FACTOR_MANUAL=supervisor`, por ejemplo, el operador conserva el ingreso por monto y la opción de factor aparece deshabilitada. Solo se aceptan `operador` y `supervisor`.

## 8. Solución de problemas

| Síntoma | Causa probable | Acción |
|---|---|---|
| El arranque falla porque el puerto 8765 está en uso | Otra instancia de la demostración sigue abierta | Cerrar esa ventana con `Ctrl+C` y volver a arrancar |
| `pip` no encuentra Flask 3.1.3 | Python distinto de 3.12 o sin acceso a PyPI | Revisar `python --version` y la conexión, y recrear `.venv` |
| La página muestra error 400 o rechaza el host | Se abrió con una IP de red en vez de `127.0.0.1` | Usar `http://127.0.0.1:8765` o `http://localhost:8765` |
| "Acceso temporalmente bloqueado" | Cinco contraseñas erradas en 60 segundos | Esperar un minuto |
| Se quiere partir de cero | La base local ya tiene cambios | Detener el servidor y borrar la carpeta `data/` |

## 9. Alcance y validación

La fórmula, los factores, la llave de negocio y los formatos de carga son demostrativos. No se usan datos reales, no existe conexión con NUAM y las credenciales de prueba no son aptas para producción. Los resultados locales no certifican infraestructura ni usabilidad con usuarios reales. La prioridad entre datos de la Bolsa y del corredor y el catálogo de instrumentos habilitados siguen pendientes de definición por NUAM. La validación docente no se acredita mediante este paquete y debe confirmarse por separado antes de presentar la solución como validada.
