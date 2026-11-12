# 3. Pruebas y resultados

## 3.1 Suites automatizadas

| Suite | Casos | Alcance |
| --- | ---: | --- |
| `tests/test_demo.py` | 40 | Dominio (U), integración (I), seguridad (S) y rendimiento (P) |
| `tests/test_ui_revision.py` | 8 | Revisión automatizada de interfaz (UI) |
| `tests/test_complementarias.py` | 10 | Casos complementarios del plan (CP): guardados concurrentes, fallos inyectados, CSRF y archivos de ejemplo |
| `tests/test_v11.py` | 10 | Regresión de la versión 1.1 (V): campo instrumento, ícono, registro operativo, permiso de factores, WSGI y modo WAL |

Cada caso crea sus propias bases y carpetas temporales. `run_all_tests.py` ejecuta las cuatro suites y deja en `evidencias/` un informe JSON y Markdown con fecha, entorno, resultado por caso y huella de las fuentes.

| Ejecución | Entorno | Resultado |
| --- | --- | --- |
| Versión 1.0, 11 de noviembre de 2026 | Windows, Python 3.12.14 | 58 de 58 |
| Versión 1.1, 11 de noviembre de 2026 | Linux, Python 3.12.3, entorno virtual nuevo | 68 de 68 |
| Versión 1.1, GitHub Actions (ejecución 2) | Windows, Python 3.12 | 65 de 68: tres casos V no cerraban la base temporal |
| Versión 1.1.1, GitHub Actions ([ejecución 3](https://github.com/YkzPam/nuam-mantenedor-tributario/actions/runs/43136203316)) | Windows con `verificar.cmd` y Ubuntu, Python 3.12 | 68 de 68 en ambos |
| Versión 1.1.1, 11 de noviembre de 2026 | Linux, Python 3.12.3 | 68 de 68 |

El flujo de GitHub Actions (`.github/workflows/verificacion.yml`) repite las cuatro suites en Windows y Ubuntu con Python 3.12 en cada cambio del repositorio. Su primera ejecución en Windows detectó que V06, V07 y V10 dejaban abierta la base SQLite temporal, lo que impedía borrar su carpeta (WinError 32); la versión 1.1.1 corrigió esas pruebas sin cambiar la aplicación.

## 3.2 Resultados frente a los esperados

| Comprobación | Esperado | Obtenido (versión 1.0, Windows) |
| --- | --- | --- |
| Consulta concurrente, 20 clientes (P01) | P95 hasta 3 s y sin HTTP 5xx | P95 de 0,027 s |
| Guardado concurrente, 20 clientes (CP01) | P95 hasta 3 s y sin HTTP 5xx | P95 de 1,027 s |
| Carga de 1.000 filas (P02) | Hasta 120 s | 0,822 s |
| Duplicados (I04, I07, I08) | Ningún duplicado activo ni carga parcial | Cumple |
| Separación por corredor (S03, S08, S14) | Rechazo de consultas y cambios ajenos | Cumple |
| Bitácora (CP06, CP08) | Evento en el 100 % de las operaciones | Cumple |

## 3.3 Prueba de estrés sostenida

`pruebas_estres.py` mantiene 20, 50 y 100 clientes durante 60 segundos por nivel, cada uno con su sesión, con 80 % de consultas y 20 % de guardados. Luego confirma diez lotes sucesivos de 1.000 filas y comprueba que las filas persistidas coincidan con las respuestas 201 y que la cadena HMAC siga válida.

| Corrida | Clientes | P95 consulta (s) | P95 guardado (s) | Respuestas 5xx |
| --- | ---: | ---: | ---: | ---: |
| Sin WAL, en proceso | 100 | 1,301 | 7,411 | 35 |
| Versión 1.1, en proceso | 100 | 0,826 | 1,994 | 0 |
| Versión 1.1, HTTP con Waitress | 100 | 0,546 | 0,530 | 0 |

Las 35 respuestas 503 sin WAL correspondieron al error `database is locked` de SQLite. Las tablas completas, con los niveles de 20 y 50 clientes y los diez lotes, están en `evidencias/`.

## 3.4 Discrepancias

| Código | Discrepancia | Estado |
| --- | --- | --- |
| D1 | Primera revisión de usabilidad bajo el 90 % (80 %) | Corregida en el código; evaluada con perfiles simulados |
| D2 | Reporte y retroalimentación basados en simulación | Abierta: falta repetir con usuarios reales |
| D3 | Atributo `pattern` del campo instrumento inválido en Chrome | Resuelta en la versión 1.1 |
| D4 | Guardado más lento que la consulta por el escritor único de SQLite | Causa confirmada; mitigada con WAL |
| D5 | Concurrencia medida solo en ráfagas | Resuelta en parte: falta el volumen real de NUAM |
| D6 | Fórmula, llave y formatos de demostración | Pendiente de NUAM |
| D7 | Prioridad entre Bolsa y corredor y catálogo de instrumentos | Pendiente de NUAM; el permiso de factores quedó configurable |
| D8 | Previsualización más lenta a medida que TinyDB acumula reportes | Abierta: se recomienda un documento independiente por lote |

El análisis completo y las recomendaciones de cada discrepancia están en el informe de pruebas extendido (`docs/Informe_pruebas_NUAM_Grupo4_extendido.docx`).
