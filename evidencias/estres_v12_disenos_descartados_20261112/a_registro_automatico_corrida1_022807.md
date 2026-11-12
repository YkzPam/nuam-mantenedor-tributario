# Prueba de estrés sostenida

Fecha UTC: 2026-11-12T02:26:31.461607+00:00
Modo: aplicación en proceso (Flask test_client) con SQLite temporal
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 30.202 | 9104 | 301.43 | 0.0838 | 0.6561 | 3.4738 | 0 |
| 50 | 30.441 | 7688 | 252.56 | 0.1355 | 3.3037 | 9.8133 | 0 |
| 100 | 31.21 | 6906 | 221.28 | 0.3418 | 7.5362 | 10.1136 | 26 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.0681 | 0.1727 | 0.0053 | 3380 | 125.0 |
| 2 | 0.0693 | 0.1847 | 0.0069 | 4380 | 125.1 |
| 3 | 0.0924 | 0.2395 | 0.0086 | 5380 | 126.3 |
| 4 | 0.1128 | 0.2125 | 0.0126 | 6380 | 127.5 |
| 5 | 0.1373 | 0.1974 | 0.0142 | 7380 | 129.6 |
| 6 | 0.1693 | 0.2089 | 0.0109 | 8380 | 131.9 |
| 7 | 0.1635 | 0.2195 | 0.0111 | 9380 | 134.7 |
| 8 | 0.1788 | 0.2382 | 0.0128 | 10380 | 137.0 |
| 9 | 0.202 | 0.2212 | 0.0138 | 11380 | 139.6 |
| 10 | 0.2137 | 0.2433 | 0.0196 | 12380 | 142.4 |

Integridad: {"guardados_201": 4697, "guardados_persistidos": 4697, "verificacion_bitacora_s": 0.342, "filas_lote_confirmadas": 10000, "filas_lote_persistidas": 10000, "eventos_auditoria": 29517, "cadena_hmac_valida": true}

Resultado global: no cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
