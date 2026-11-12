# Prueba de estrés sostenida

Fecha UTC: 2026-11-12T02:53:55.060201+00:00
Modo: aplicación en proceso (Flask test_client) con SQLite temporal
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 60.067 | 17529 | 291.82 | 0.1019 | 0.1498 | 1.3565 | 0 |
| 50 | 60.22 | 13606 | 225.94 | 0.336 | 0.6532 | 2.9575 | 0 |
| 100 | 60.806 | 11215 | 184.44 | 0.7701 | 3.3694 | 10.297 | 1 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.0825 | 0.1291 | 0.0088 | 5168 | 213.3 |
| 2 | 0.0759 | 0.1407 | 0.0097 | 6168 | 213.3 |
| 3 | 0.099 | 0.1601 | 0.0138 | 7168 | 213.3 |
| 4 | 0.1185 | 0.1447 | 0.0115 | 8168 | 213.3 |
| 5 | 0.1348 | 0.1434 | 0.0123 | 9168 | 214.1 |
| 6 | 0.1583 | 0.168 | 0.0131 | 10168 | 217.7 |
| 7 | 0.1748 | 0.1644 | 0.0127 | 11168 | 220.2 |
| 8 | 0.1758 | 0.1703 | 0.0145 | 12168 | 222.7 |
| 9 | 0.1976 | 0.1848 | 0.0217 | 13168 | 224.6 |
| 10 | 0.2168 | 0.1851 | 0.0165 | 14168 | 226.8 |

Integridad: {"guardados_201": 8386, "guardados_persistidos": 8386, "verificacion_bitacora_s": 0.2442, "filas_lote_confirmadas": 10000, "filas_lote_persistidas": 10000, "eventos_auditoria": 18509, "cadena_hmac_valida": true}

Resultado global: no cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
