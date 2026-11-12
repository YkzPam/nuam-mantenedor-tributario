# Prueba de estrés sostenida

Fecha UTC: 2026-11-12T06:05:43.976459+00:00
Modo: aplicación en proceso (Flask test_client) con SQLite temporal
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 60.122 | 15011 | 249.68 | 0.12 | 0.1595 | 1.4207 | 0 |
| 50 | 60.2 | 11994 | 199.24 | 0.3775 | 0.749 | 3.3042 | 0 |
| 100 | 60.696 | 10192 | 167.92 | 0.9232 | 3.0281 | 10.4988 | 1 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.0846 | 0.1728 | 0.0102 | 4657 | 197.1 |
| 2 | 0.0903 | 0.1259 | 0.0093 | 5657 | 197.1 |
| 3 | 0.1336 | 0.1414 | 0.0097 | 6657 | 197.1 |
| 4 | 0.1156 | 0.1497 | 0.0112 | 7657 | 198.0 |
| 5 | 0.1453 | 0.1509 | 0.0115 | 8657 | 198.8 |
| 6 | 0.1521 | 0.1601 | 0.0125 | 9657 | 202.6 |
| 7 | 0.17 | 0.218 | 0.0149 | 10657 | 205.2 |
| 8 | 0.1878 | 0.2118 | 0.0204 | 11657 | 207.6 |
| 9 | 0.2327 | 0.2307 | 0.0161 | 12657 | 210.5 |
| 10 | 0.2319 | 0.2616 | 0.0169 | 13657 | 211.7 |

Integridad: {"guardados_201": 7389, "guardados_persistidos": 7389, "verificacion_bitacora_s": 0.2621, "filas_lote_confirmadas": 10000, "filas_lote_persistidas": 10000, "eventos_auditoria": 17512, "cadena_hmac_valida": true}

Resultado global: no cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
