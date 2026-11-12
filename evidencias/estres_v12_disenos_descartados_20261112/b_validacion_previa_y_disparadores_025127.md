# Prueba de estrés sostenida

Fecha UTC: 2026-11-12T02:48:23.075674+00:00
Modo: aplicación en proceso (Flask test_client) con SQLite temporal
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 60.062 | 16995 | 282.96 | 0.1039 | 0.1615 | 1.2105 | 0 |
| 50 | 60.194 | 13462 | 223.65 | 0.3377 | 0.6104 | 3.631 | 0 |
| 100 | 60.594 | 11543 | 190.5 | 0.7323 | 3.5356 | 10.3689 | 1 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.0982 | 0.1269 | 0.0095 | 5189 | 215.7 |
| 2 | 0.0691 | 0.1781 | 0.0092 | 6189 | 215.7 |
| 3 | 0.0935 | 0.1359 | 0.01 | 7189 | 216.0 |
| 4 | 0.1159 | 0.1403 | 0.0113 | 8189 | 216.3 |
| 5 | 0.1285 | 0.1529 | 0.0128 | 9189 | 217.5 |
| 6 | 0.1616 | 0.1671 | 0.0137 | 10189 | 219.5 |
| 7 | 0.1709 | 0.1925 | 0.0183 | 11189 | 222.0 |
| 8 | 0.1821 | 0.1743 | 0.0119 | 12189 | 225.1 |
| 9 | 0.1799 | 0.187 | 0.0161 | 13189 | 226.3 |
| 10 | 0.2101 | 0.1811 | 0.0167 | 14189 | 228.5 |

Integridad: {"guardados_201": 8337, "guardados_persistidos": 8337, "verificacion_bitacora_s": 0.1905, "filas_lote_confirmadas": 10000, "filas_lote_persistidas": 10000, "eventos_auditoria": 18460, "cadena_hmac_valida": true}

Resultado global: no cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
