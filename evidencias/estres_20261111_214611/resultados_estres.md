# Prueba de estrés sostenida

Fecha UTC: 2026-11-11T21:43:07.503069+00:00
Modo: HTTP contra http://127.0.0.1:8765
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 60.077 | 18300 | 304.61 | 0.0938 | 0.094 | 0.294 | 0 |
| 50 | 60.194 | 14637 | 243.16 | 0.2591 | 0.2492 | 0.3638 | 0 |
| 100 | 60.516 | 13411 | 221.61 | 0.5458 | 0.5299 | 0.8964 | 0 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.0571 | 0.0914 | 0.0082 | 5572 | - |
| 2 | 0.0631 | 0.1183 | 0.0093 | 6572 | - |
| 3 | 0.0772 | 0.1038 | 0.0093 | 7572 | - |
| 4 | 0.0844 | 0.1133 | 0.0099 | 8572 | - |
| 5 | 0.0985 | 0.1188 | 0.0111 | 9572 | - |
| 6 | 0.1204 | 0.1309 | 0.0134 | 10572 | - |
| 7 | 0.1648 | 0.1359 | 0.0126 | 11572 | - |
| 8 | 0.1543 | 0.1422 | 0.0134 | 12572 | - |
| 9 | 0.1974 | 0.1599 | 0.0138 | 13572 | - |
| 10 | 0.1754 | 0.1739 | 0.0158 | 14572 | - |

Integridad: {"guardados_201": 9190, "guardados_persistidos": 9190, "verificacion_bitacora_s": 0.234, "filas_lote_confirmadas": 10000, "filas_lote_persistidas": 10000, "eventos_auditoria": null, "cadena_hmac_valida": true}

Resultado global: cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
