# Evidencias de las versiones 1.1 a 1.2.1

Ejecuciones del 11 y 12 de noviembre de 2026 (hora de Chile; los nombres de carpeta usan la fecha UTC) en Linux con Python 3.12.3 y las dependencias de `requirements-lock.txt` y `requirements-servidor.txt`, instaladas en un entorno nuevo. Al volver a ejecutar las pruebas se agregan carpetas nuevas con su propia fecha; las de esta lista no se reemplazan.

| Carpeta | Contenido |
|---|---|
| `ejecucion_completa_20261111_214727_152229` | `run_all_tests.py`: 68 de 68 casos, con resultado, duración y detalle por caso y huella SHA-256 de las fuentes |
| `estres_sin_wal_20261111_213848` | Línea base: mismo código y misma prueba sin `PRAGMA journal_mode=WAL`. Con 100 clientes, P95 de guardado de 7,41 s y 35 respuestas 503 |
| `estres_20261111_214239` | Versión 1.1 en proceso, 60 s por nivel y diez lotes de 1.000 filas |
| `estres_20261111_214611` | Versión 1.1 por HTTP contra Waitress 3.0.2 con ocho hilos y una carpeta de datos desechable |
| `chrome_d3_20261111` | Chrome 153: consola y validación del campo instrumento en v1.0 y v1.1, más la captura del aviso en pantalla |
| `ejecucion_completa_20261112_014542_576470` | Versión 1.1.1 en Linux con Python 3.12.3: 68 de 68, después de cerrar las conexiones SQLite de `test_v11.py` |
| `github_actions_20261112` | Capturas de `verificar.cmd` en Windows: [ejecución 3](https://github.com/YkzPam/nuam-mantenedor-tributario/actions/runs/43136203316) con 68 de 68 (versión 1.1.1) y [ejecución 24](https://github.com/YkzPam/nuam-mantenedor-tributario/actions/runs/43169732121) con 86 de 86 (versión 1.2) |
| `ejecucion_completa_20261112_062347_060112` | Versión 1.2 en Linux con Python 3.12.3: 86 de 86, con la suite `test_v12.py` (W01 a W18) |
| `estres_20261112_061749` | Versión 1.2 en proceso, 60 s por nivel y diez lotes. Con 100 clientes, P95 de guardado de 1,549 s y ninguna respuesta 5xx |
| `estres_20261112_062204` | Versión 1.2 por HTTP contra Waitress 3.0.2 con ocho hilos. Con 100 clientes, P95 de guardado de 0,637 s y ninguna respuesta 5xx |
| `estres_v111_mismo_equipo_20261112` | Versión 1.1.1 medida en el mismo equipo que la 1.2, como referencia (30 y 60 s por nivel) |
| `estres_v12_disenos_descartados_20261112` | Cuatro diseños de la regla DEMO-2 descartados por la prueba de estrés; `NOTA.md` resume cada uno |
| `docker_20261113` | Versión 1.2.1: construcción de la imagen con Docker 29.9.3, 86 de 86 pruebas dentro del contenedor y prueba de humo con volumen persistente; `NOTA.md` explica el uso del proxy durante la construcción |
| `chrome_v12_20261112` | Recorrido de la versión 1.2 con Chrome sin cabeza: catálogo, carga de Bolsa, rechazos por catálogo, botones del operador y sugerencia del formulario. Incluye el script que lo generó y su registro; la consola no mostró errores |

Las tres corridas de estrés se hicieron antes de agregar el texto de ayuda (`title`) del campo instrumento. Ese cambio afecta solo al HTML; la ejecución completa de 68 casos y la revisión en Chrome son posteriores a él. La versión 1.1.1 no modificó el código de la aplicación, por lo que las corridas de estrés siguen siendo válidas para ella.

Durante la corrida por HTTP, Waitress registró avisos de que alcanzó su límite predeterminado de 100 conexiones simultáneas y una cola de hasta 92 tareas para ocho hilos. No hubo respuestas 5xx; el efecto fue espera en cola, incluida en los tiempos medidos. La memoria residente del proceso de Waitress al terminar fue de 133 MiB, con un máximo de 141 MiB (VmRSS y VmHWM).

En la versión 1.2, la carpeta de estrés en proceso y la ejecución completa corresponden al código entregado. El recorrido en Chrome se repitió con ese mismo código. Las corridas de `estres_v12_disenos_descartados_20261112` se hicieron con variantes que no forman parte del paquete.

El 12 de noviembre, en los tres archivos `resultados_corregidos.json`, las rutas absolutas del equipo donde se ejecutaron las pruebas se reemplazaron por `<carpeta-de-trabajo>`. El resto del contenido no cambió, pero la huella SHA-256 de esos tres archivos ya no coincide con la que registran los manifiestos de versiones anteriores.

Límites: datos ficticios, un solo equipo, clientes generados en el mismo equipo y SQLite local. Los resultados no reemplazan una prueba en la infraestructura de NUAM.
