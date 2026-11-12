# Prueba de estrés sostenida

Fecha UTC: 2026-11-12T02:34:53.536001+00:00
Modo: aplicación en proceso (Flask test_client) con SQLite temporal
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 30.284 | 8437 | 278.59 | 0.077 | 0.8919 | 3.6815 | 0 |
| 50 | 30.483 | 7165 | 235.05 | 0.1854 | 3.3086 | 9.049 | 0 |
| 100 | 30.821 | 6677 | 216.64 | 0.3679 | 7.6573 | 10.3776 | 28 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.064 | 0.1387 | 0.006 | 3166 | 125.6 |

Integridad: {"guardados_201": 4426, "guardados_persistidos": 4426, "verificacion_bitacora_s": 0.1388, "filas_lote_confirmadas": 1000, "filas_lote_persistidas": 1000, "eventos_auditoria": 10957, "cadena_hmac_valida": true}

Resultado global: no cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
