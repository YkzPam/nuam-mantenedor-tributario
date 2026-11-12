# Prueba de estrés sostenida

Fecha UTC: 2026-11-12T06:14:44.101336+00:00
Modo: aplicación en proceso (Flask test_client) con SQLite temporal
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 60.061 | 13992 | 232.96 | 0.1281 | 0.1714 | 1.7333 | 0 |
| 50 | 60.196 | 12049 | 200.16 | 0.3974 | 0.5058 | 3.4288 | 0 |
| 100 | 60.489 | 10785 | 178.3 | 0.9468 | 1.5494 | 6.3621 | 0 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.0934 | 0.1082 | 0.0087 | 4708 | 201.7 |
| 2 | 0.1219 | 0.1869 | 0.013 | 5708 | 201.7 |
| 3 | 0.1396 | 0.1518 | 0.0106 | 6708 | 201.7 |
| 4 | 0.1167 | 0.1642 | 0.0116 | 7708 | 201.8 |
| 5 | 0.1471 | 0.1636 | 0.0117 | 8708 | 204.2 |
| 6 | 0.1511 | 0.1748 | 0.0143 | 9708 | 205.4 |
| 7 | 0.203 | 0.2489 | 0.0198 | 10708 | 207.8 |
| 8 | 0.3054 | 0.2287 | 0.0166 | 11708 | 209.7 |
| 9 | 0.2258 | 0.2116 | 0.0191 | 12708 | 211.8 |
| 10 | 0.2695 | 0.2128 | 0.02 | 13708 | 218.3 |

Integridad: {"guardados_201": 7302, "guardados_persistidos": 7302, "verificacion_bitacora_s": 0.2271, "filas_lote_confirmadas": 10000, "filas_lote_persistidas": 10000, "eventos_auditoria": 17425, "cadena_hmac_valida": true}

Resultado global: cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
