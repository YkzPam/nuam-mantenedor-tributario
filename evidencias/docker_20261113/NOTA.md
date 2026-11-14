# Verificación del contenedor — 13 de noviembre de 2026

Imagen construida desde el `Dockerfile` del paquete con Docker 29.9.3 en Linux.

| Archivo | Contenido |
|---|---|
| `construccion.log` | Salida completa de `docker build` |
| `imagen.txt` | Identificador y tamaño de la imagen, usuario, comando y versiones de Python, Flask, Werkzeug, TinyDB y Waitress dentro del contenedor |
| `pruebas_dentro_del_contenedor.txt` | `python -m unittest discover -s tests -v` dentro de la imagen: 86 de 86 casos |
| `prueba_humo_docker.py` | Script de la prueba de humo contra el contenedor publicado en `127.0.0.1:8765` |
| `prueba_humo.json` | Resultado de los seis puntos de la prueba de humo |

Comandos usados:

```bash
docker build -t nuam-mantenedor:1.2 .
docker volume create nuam-datos
docker run -d --name nuam -p 127.0.0.1:8765:8765 -v nuam-datos:/datos nuam-mantenedor:1.2
python prueba_humo_docker.py prueba_humo.json
docker run --rm -e NUAM_DATA_DIR=/tmp/d nuam-mantenedor:1.2 python -m unittest discover -s tests -v
```

Diferencia con un equipo común: la red del equipo de construcción pasa por un proxy con certificado propio. La construcción usó `--network host` y una copia del `Dockerfile` (`Dockerfile.sandbox`, como aparece en `construccion.log`) que solo cambia la línea de `pip install` para entregar ese certificado como secreto de construcción:

```dockerfile
RUN --mount=type=secret,id=ca,target=/tmp/ca.crt PIP_CERT=/tmp/ca.crt pip install --no-cache-dir -r requirements-lock.txt -r requirements-servidor.txt
```

El certificado no queda en ninguna capa de la imagen; el historial solo conserva la ruta `/tmp/ca.crt`. El resto de las instrucciones es idéntico. En un equipo con acceso directo a internet basta el primer comando.

Tanto las pruebas como la aplicación publicada se ejecutaron con el usuario sin privilegios `nuam` que define el `Dockerfile`.

## Versión 1.2.2

La imagen se reconstruyó el mismo día con el código de la versión 1.2.2 (`v1_2_2/`), con el mismo procedimiento. `run_all_tests.py` aprobó 88 de 88 dentro de esa imagen (`evidencias/ejecucion_completa_20261113_185008_912162`) y la prueba de humo volvió a aprobar sus seis comprobaciones.

## Versión 1.2.4

Reconstrucción del 14 de noviembre con el código de la versión 1.2.4 (`v1_2_4/`). `run_all_tests.py` aprobó 90 de 90 dentro de esa imagen (`evidencias/ejecucion_completa_20261114_153652_447706`) y la prueba de humo aprobó sus seis comprobaciones.
