# Historial de versiones

## 1.1.1 — 11 de noviembre de 2026

Origen: primera ejecución de las pruebas en GitHub Actions con Windows.

Corregido

- En Windows, V06, V07 y V10 dejaban abierta la base SQLite temporal y `tearDown` no podía borrar su carpeta (WinError 32), con 65 de 68 casos aprobados ([ejecución 2](https://github.com/YkzPam/nuam-mantenedor-tributario/actions/runs/43135705148)). Las consultas directas de `tests/test_v11.py` usan ahora `contextlib.closing`. La aplicación no cambió.

Agregado

- `preparar.cmd`, `iniciar.cmd` y `verificar.cmd` para Windows, y `.gitattributes` para conservar sus finales de línea CRLF.
- `README.md` y guías numeradas en `docs/`: arquitectura y datos, seguridad, pruebas y resultados, rúbrica y verificación.
- `.github/workflows/verificacion.yml`: ejecuta las cuatro suites en Windows, mediante `verificar.cmd`, y en Ubuntu, con Python 3.12.

Verificación

- GitHub Actions: 68 de 68 en Windows y en Ubuntu ([ejecución 3](https://github.com/YkzPam/nuam-mantenedor-tributario/actions/runs/43136203316)). Con esto se cumple la repetición en Windows que la versión 1.1 dejó pendiente.
- Linux, Python 3.12.3: 68 de 68 (`evidencias/ejecucion_completa_20261112_014542_576470`).

## 1.1 — 11 de noviembre de 2026

Origen: discrepancias D3 y D5 del informe de pruebas de la Unidad 3 y revisión del paquete frente a la rúbrica.

Corregido

- D3: el atributo `pattern` del campo Instrumento ficticio escapa el guion (`[A-Za-z0-9._\-]`). Chrome 153 ya no informa la expresión como inválida y el aviso aparece en pantalla antes de enviar. El campo agrega un texto de ayuda en español.
- La página declara un ícono embebido (`data:`), por lo que el navegador deja de pedir `/favicon.ico` y desaparece el error 404 de la consola.

Agregado

- Registro operativo en `data/logs/operacion.log`: fecha, método, ruta declarada, estado HTTP, duración y perfil, sin cuerpos, búsquedas, cookies, tokens ni contraseñas. Rota a los 5 MB y conserva tres archivos anteriores.
- Variable `NUAM_ROLES_FACTOR_MANUAL` para limitar el ingreso manual de factores (formulario y cargas `factores-DEMO`). Sin la variable rige la matriz de la Unidad 2. Un intento denegado queda en la bitácora como `factor_manual_denegado`.
- `wsgi.py` y `requirements-servidor.txt` (Waitress 3.0.2), con `NUAM_DATA_DIR` para separar datos y código.
- `Dockerfile` y `.dockerignore`. No se construyó la imagen: el equipo de prueba no tenía el servicio de Docker.
- `pruebas_estres.py`: carga mixta sostenida con 20, 50 y 100 clientes, lotes sucesivos de 1.000 filas, memoria del proceso e integridad de datos y bitácora. Funciona en proceso o contra un servidor por HTTP.
- Suite `tests/test_v11.py` con diez casos (V01 a V10). El total pasa de 58 a 68 casos.
- `CONTRIBUTING.md`, `.gitignore` e instrucciones ampliadas en `INICIO_UNIDAD3.md` (Linux y macOS, usuarios, Waitress, Docker, estrés, registro y solución de problemas).

Optimizado

- SQLite trabaja en modo WAL. Con 100 clientes en proceso y 60 segundos por nivel, el P95 de guardado bajó de 7,41 s con 35 respuestas 503 a 1,99 s sin respuestas 5xx (`evidencias/estres_sin_wal_20261111_213848` frente a `evidencias/estres_20261111_214239`).

Verificación

- 68 de 68 casos aprobados con Python 3.12.3 en Linux (`evidencias/ejecucion_completa_*`).
- Estrés en proceso y por HTTP contra Waitress con ocho hilos: P95 de consultas y guardados bajo 3 s en los tres niveles, sin respuestas 5xx, filas persistidas iguales a las respuestas 201 y cadena HMAC válida.
- Chrome 153: sin mensajes en consola en v1.1; en v1.0 se reprodujeron el error del `pattern` y el 404 del ícono (`evidencias/chrome_d3_20261111`).

Pendiente

- Repetir la ejecución de v1.1 en Windows con Python 3.12, el entorno de la ejecución de v1.0.
- Prioridad entre datos de la Bolsa y del corredor, y catálogo de instrumentos habilitados (D7): requieren definición de NUAM.
- Los reportes en TinyDB se leen y reescriben completos; la previsualización de un lote de 1.000 filas pasó de 0,05 s a 0,19 s tras diez lotes.

## 1.0 — paquete de la Unidad 3

Cambios registrados en las evidencias de la Unidad 2 y antes de la entrega de la Unidad 3:

- 6 de octubre: la acción Inactivar pasa a llamarse Desactivar y la confirmación identifica el registro (UX01; UI01 a UI03).
- 6 de octubre: Cancelar en verde sólido y "Sí, desactivar" con borde rojo (UX02; UI07).
- 6 de octubre: los campos obligatorios rechazan nulos, booleanos y colecciones (MA01, MA02).
- 7 de octubre: el guardado por API evita el envío nativo del formulario; CSV y huellas largas se ajustan al ancho de pantalla.
- 7 de octubre: el resumen de carga se actualiza solo después de una confirmación exitosa (D1; UI08).
- 11 de noviembre: ejecución final, 58 de 58 casos aprobados en Windows con Python 3.12.
