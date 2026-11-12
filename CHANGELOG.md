# Historial de versiones

## 1.2 — 12 de noviembre de 2026

Origen: discrepancia D7. La prioridad entre Bolsa y corredor y el catálogo de instrumentos esperaban una definición de NUAM; el docente autorizó que el equipo las definiera para completar la demostración. Ambas reglas quedan pendientes de validación de NUAM.

Agregado

- Regla DEMO-2, catálogo de instrumentos. Tabla `instrumento` por mercado, con inscripción, estado y versión. Un inscrito debe figurar habilitado; un no inscrito fuera del catálogo se admite y, si figura, debe coincidir y estar habilitado. Se valida al crear, modificar, prevalidar y confirmar; en las escrituras, la condición va dentro de la misma sentencia `INSERT` o `UPDATE`. El supervisor agrega, deshabilita y habilita instrumentos (`/api/instruments`), y cada cambio queda en la bitácora. Nueva vista "Catálogo de instrumentos" y sugerencia de inscripción en el formulario.
- Regla DEMO-3, prioridad de la Bolsa. Tipo de carga y origen `bolsa-DEMO`, solo para el supervisor y en modo factor. Una fila de Bolsa reemplaza el registro del corredor con la misma llave, conserva su identificador y deja los valores anteriores en el evento `prioridad_bolsa`. El registro manual y las cargas del corredor no pueden reemplazarlo, y el operador no puede modificarlo ni desactivarlo. La consulta muestra la marca "Prioridad Bolsa".
- `ejemplos/06_bolsa_prioridad.csv` y `ejemplos/07_catalogo_rechazos.csv`.
- Suite `tests/test_v12.py` con 18 casos (W01 a W18). El total pasa de 68 a 86 casos.
- Respaldo automático: una base con esquema anterior se mueve, con sus archivos privados, a `data/respaldo_v1_<fecha>/` y se crea el esquema 2 (`PRAGMA user_version = 2`).
- `evidencias/chrome_v12_20261112`: recorrido de la interfaz con Chrome sin cabeza, capturas y el script que lo generó.

Cambiado

- Ocho definiciones de filas de prueba en `tests/test_demo.py` (casos I08, I10, I12, P02, S08, S15 y S16) y las filas de los lotes de `pruebas_estres.py` declaraban inscritos instrumentos inventados. Con DEMO-2 se rechazarían por el catálogo y algunas pruebas pasarían por un motivo distinto del que verifican, por lo que ahora se declaran no inscritas. Lo que cada prueba comprueba no cambió.
- La prueba de estrés descartó cuatro diseños previos de DEMO-2. Agregar al catálogo cada no inscrito nuevo, con un segundo evento de bitácora, llevó el P95 de guardado con 100 clientes a entre 7,2 y 7,7 s, con 26 a 29 respuestas 5xx. Las variantes con una consulta previa al catálogo o con disparadores de SQLite quedaron entre 3,0 y 3,5 s, con una respuesta 5xx cada una. La versión entregada evalúa la regla dentro de la sentencia de escritura y midió 1,549 s sin respuestas 5xx, frente a 1,491 s de la 1.1.1 en el mismo equipo (`evidencias/estres_v12_disenos_descartados_20261112`).

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
