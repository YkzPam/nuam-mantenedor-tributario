# Prueba de estrés sostenida

Fecha UTC: 2026-11-11T21:35:43.720222+00:00
Modo: aplicación en proceso (Flask test_client) con SQLite temporal
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 60.186 | 16994 | 282.36 | 0.1636 | 0.599 | 2.8862 | 0 |
| 50 | 60.478 | 11935 | 197.34 | 0.746 | 2.3969 | 9.8789 | 0 |
| 100 | 61.149 | 9428 | 154.18 | 1.3013 | 7.4114 | 11.2835 | 35 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.0567 | 0.113 | 0.0065 | 4809 | 160.9 |
| 2 | 0.0612 | 0.0959 | 0.0077 | 5809 | 160.9 |
| 3 | 0.0807 | 0.1302 | 0.0082 | 6809 | 162.1 |
| 4 | 0.0906 | 0.1115 | 0.0087 | 7809 | 163.2 |
| 5 | 0.1103 | 0.1382 | 0.0093 | 8809 | 164.4 |
| 6 | 0.1158 | 0.1241 | 0.0102 | 9809 | 166.6 |
| 7 | 0.1335 | 0.1277 | 0.0107 | 10809 | 169.4 |
| 8 | 0.1441 | 0.1358 | 0.0114 | 11809 | 171.6 |
| 9 | 0.1612 | 0.1388 | 0.0121 | 12809 | 173.7 |
| 10 | 0.1728 | 0.1444 | 0.0128 | 13809 | 175.9 |

Integridad: {"guardados_201": 7716, "guardados_persistidos": 7716, "verificacion_bitacora_s": 0.1849, "filas_lote_confirmadas": 10000, "filas_lote_persistidas": 10000, "eventos_auditoria": 17839, "cadena_hmac_valida": true}

Resultado global: no cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
