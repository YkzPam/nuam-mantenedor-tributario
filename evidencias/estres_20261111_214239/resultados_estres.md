# Prueba de estrés sostenida

Fecha UTC: 2026-11-11T21:39:36.049228+00:00
Modo: aplicación en proceso (Flask test_client) con SQLite temporal
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 60.089 | 18396 | 306.15 | 0.1055 | 0.1333 | 0.9707 | 0 |
| 50 | 60.113 | 14578 | 242.51 | 0.3307 | 0.3807 | 1.9274 | 0 |
| 100 | 60.46 | 12001 | 198.5 | 0.8257 | 1.9935 | 10.3947 | 0 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.0501 | 0.0933 | 0.0075 | 5542 | 226.3 |
| 2 | 0.0598 | 0.103 | 0.0081 | 6542 | 226.3 |
| 3 | 0.0781 | 0.1172 | 0.0089 | 7542 | 226.3 |
| 4 | 0.0858 | 0.1132 | 0.0098 | 8542 | 226.3 |
| 5 | 0.1024 | 0.1215 | 0.0104 | 9542 | 226.3 |
| 6 | 0.1168 | 0.1316 | 0.0118 | 10542 | 229.8 |
| 7 | 0.1433 | 0.1341 | 0.012 | 11542 | 232.2 |
| 8 | 0.1437 | 0.1418 | 0.0124 | 12542 | 234.7 |
| 9 | 0.1572 | 0.1454 | 0.0176 | 13542 | 237.4 |
| 10 | 0.1901 | 0.1775 | 0.014 | 14542 | 239.6 |

Integridad: {"guardados_201": 8953, "guardados_persistidos": 8953, "verificacion_bitacora_s": 0.2014, "filas_lote_confirmadas": 10000, "filas_lote_persistidas": 10000, "eventos_auditoria": 19076, "cadena_hmac_valida": true}

Resultado global: cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
