# Diseños descartados de la regla DEMO-2

Las corridas de esta carpeta se hicieron el 12 de noviembre de 2026 (UTC) con variantes de la versión 1.2 que no forman parte del paquete. Todas usaron `pruebas_estres.py` dentro del proceso, en el mismo equipo y con 20, 50 y 100 clientes. El script usa un instrumento distinto en cada guardado, por lo que cada solicitud valida un código que no está en el catálogo.

| Variante | Qué hacía cada guardado | Segundos por nivel | P95 de guardado con 100 clientes (s) | 5xx con 100 clientes |
|---|---|---:|---:|---:|
| A, corrida 1 (`022807`) | Agregaba el código al catálogo y escribía un segundo evento de bitácora | 30 | 7,536 | 26 |
| A, corrida 2 (`023437`) | Igual | 30 | 7,220 | 29 |
| A, corrida 3 (`023625`) | Igual | 30 | 7,657 | 28 |
| B (`025127`) | Consultaba catálogo y llave antes de escribir; disparadores de SQLite en la tabla | 60 | 3,536 | 1 |
| C (`025659`) | Solo disparadores de SQLite; consultas únicamente después de un rechazo | 60 | 3,369 | 1 |
| D (`060848`) | Solo una consulta al catálogo antes de escribir | 60 | 3,028 | 1 |

En las variantes B, C y D cada respuesta 5xx fue un guardado que esperó más que el límite de 10 segundos de la conexión, el mismo mecanismo descrito para la corrida sin WAL de la versión 1.1. La versión 1.1.1, medida en el mismo equipo, tuvo 0,794 s con 30 segundos por nivel y 1,491 s con 60 segundos, sin respuestas 5xx (`../estres_v111_mismo_equipo_20261112`).

La versión entregada evalúa la regla DEMO-2 dentro de la misma sentencia `INSERT` o `UPDATE`, con una condición sobre la tabla `instrumento`, y solo consulta el catálogo para explicar un rechazo. Su corrida de 60 segundos por nivel (`../estres_20261112_061749`) tuvo 1,549 s con 100 clientes y ninguna respuesta 5xx. Estas mediciones no aíslan por separado el costo de cada consulta o disparador: muestran que las variantes con trabajo adicional por guardado quedaron sobre el umbral de 3 segundos y que la versión entregada volvió a valores cercanos a los de la 1.1.1. Entre corridas de una misma versión también hay variación; la 1.1 midió 1,994 s el 11 de noviembre.
