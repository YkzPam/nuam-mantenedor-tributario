# Prueba de estrés sostenida

Fecha UTC: 2026-11-12T02:33:05.550477+00:00
Modo: aplicación en proceso (Flask test_client) con SQLite temporal
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 30.258 | 8386 | 277.15 | 0.0885 | 0.6926 | 5.0771 | 0 |
| 50 | 30.471 | 7062 | 231.77 | 0.2018 | 2.9788 | 10.1439 | 1 |
| 100 | 31.018 | 6779 | 218.55 | 0.319 | 7.2196 | 10.1451 | 29 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.0681 | 0.1865 | 0.009 | 3175 | 125.3 |

Integridad: {"guardados_201": 4310, "guardados_persistidos": 4310, "verificacion_bitacora_s": 0.1928, "filas_lote_confirmadas": 1000, "filas_lote_persistidas": 1000, "eventos_auditoria": 10725, "cadena_hmac_valida": true}

Resultado global: no cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
