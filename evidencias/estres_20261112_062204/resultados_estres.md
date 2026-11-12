# Prueba de estrés sostenida

Fecha UTC: 2026-11-12T06:18:58.819706+00:00
Modo: HTTP contra http://127.0.0.1:8765
Python 3.12.3 · Linux-6.18.44-fc-v378-x86_64-with-glibc2.39

| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 20 | 60.093 | 14419 | 239.95 | 0.1135 | 0.1121 | 0.2171 | 0 |
| 50 | 60.245 | 12312 | 204.37 | 0.2951 | 0.2851 | 0.4167 | 0 |
| 100 | 60.677 | 10880 | 179.31 | 0.6638 | 0.6367 | 0.8673 | 0 |

| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.0689 | 0.1592 | 0.0093 | 4864 | - |
| 2 | 0.1012 | 0.133 | 0.0108 | 5864 | - |
| 3 | 0.1172 | 0.1673 | 0.0112 | 6864 | - |
| 4 | 0.1312 | 0.1922 | 0.0124 | 7864 | - |
| 5 | 0.182 | 0.1731 | 0.0138 | 8864 | - |
| 6 | 0.2133 | 0.1763 | 0.0143 | 9864 | - |
| 7 | 0.2482 | 0.2294 | 0.0154 | 10864 | - |
| 8 | 0.2133 | 0.2684 | 0.0271 | 11864 | - |
| 9 | 0.2479 | 0.2162 | 0.0172 | 12864 | - |
| 10 | 0.2505 | 0.2167 | 0.0215 | 13864 | - |

Integridad: {"guardados_201": 7564, "guardados_persistidos": 7564, "verificacion_bitacora_s": 0.2577, "filas_lote_confirmadas": 10000, "filas_lote_persistidas": 10000, "eventos_auditoria": null, "cadena_hmac_valida": true}

Resultado global: cumple los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).

Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM.
