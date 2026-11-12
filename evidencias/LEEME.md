# Evidencias de las versiones 1.1 y 1.1.1

Ejecuciones del 11 de noviembre de 2026 (hora de Chile) en Linux con Python 3.12.3 y las dependencias de `requirements-lock.txt` y `requirements-servidor.txt`, instaladas en un entorno nuevo. Al volver a ejecutar las pruebas se agregan carpetas nuevas con su propia fecha; las de esta lista no se reemplazan.

| Carpeta | Contenido |
|---|---|
| `ejecucion_completa_20261111_214727_152229` | `run_all_tests.py`: 68 de 68 casos, con resultado, duración y detalle por caso y huella SHA-256 de las fuentes |
| `estres_sin_wal_20261111_213848` | Línea base: mismo código y misma prueba sin `PRAGMA journal_mode=WAL`. Con 100 clientes, P95 de guardado de 7,41 s y 35 respuestas 503 |
| `estres_20261111_214239` | Versión 1.1 en proceso, 60 s por nivel y diez lotes de 1.000 filas |
| `estres_20261111_214611` | Versión 1.1 por HTTP contra Waitress 3.0.2 con ocho hilos y una carpeta de datos desechable |
| `chrome_d3_20261111` | Chrome 153: consola y validación del campo instrumento en v1.0 y v1.1, más la captura del aviso en pantalla |
| `ejecucion_completa_20261112_014542_576470` | Versión 1.1.1 en Linux con Python 3.12.3: 68 de 68, después de cerrar las conexiones SQLite de `test_v11.py` |
| `github_actions_20261112` | Captura de la [ejecución 3 de GitHub Actions](https://github.com/YkzPam/nuam-mantenedor-tributario/actions/runs/43136203316): `verificar.cmd` en Windows con 68 de 68 |

Las tres corridas de estrés se hicieron antes de agregar el texto de ayuda (`title`) del campo instrumento. Ese cambio afecta solo al HTML; la ejecución completa de 68 casos y la revisión en Chrome son posteriores a él. La versión 1.1.1 no modificó el código de la aplicación, por lo que las corridas de estrés siguen siendo válidas para ella.

Durante la corrida por HTTP, Waitress registró avisos de que alcanzó su límite predeterminado de 100 conexiones simultáneas y una cola de hasta 92 tareas para ocho hilos. No hubo respuestas 5xx; el efecto fue espera en cola, incluida en los tiempos medidos. La memoria residente del proceso de Waitress al terminar fue de 133 MiB, con un máximo de 141 MiB (VmRSS y VmHWM).

Límites: datos ficticios, un solo equipo, clientes generados en el mismo equipo y SQLite local. Los resultados no reemplazan una prueba en la infraestructura de NUAM.
