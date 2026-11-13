# 5. Verificación del paquete

## 5.1 Integridad de los archivos

El paquete entregado en DreamShaper es `NUAM_Unidad_3_Implementacion_v1.2.zip`. Su huella SHA-256 está en el Anexo B del documento de asesoría, porque no puede incluirse dentro del mismo ZIP. `MANIFIESTO_SHA256.json` registra el tamaño y la huella de cada archivo del paquete e indica los que cambiaron o se agregaron respecto de la versión 1.1.1. En PowerShell, la huella de un archivo se obtiene con:

```powershell
Get-FileHash .\app.py -Algorithm SHA256
```

El ZIP contiene los mismos archivos del repositorio, salvo los dos documentos `.docx` de `docs/`, que se entregan por separado en DreamShaper.

## 5.2 Pruebas

```powershell
verificar.cmd
```

El acceso prepara el entorno si falta y ejecuta `run_all_tests.py`. El resultado esperado es `"tests": 88, "passed": 88, "failed": 0, "errors": 0`, con un informe nuevo en `evidencias/`.

## 5.3 Estrés y servidor WSGI

```powershell
.\.venv\Scripts\python.exe pruebas_estres.py --segundos 60
.\.venv\Scripts\python.exe -m pip install -r requirements-servidor.txt
.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8765 --threads=8 wsgi:app
```

Para medir por HTTP, iniciar Waitress con `NUAM_DATA_DIR` apuntando a una carpeta desechable y ejecutar `pruebas_estres.py --url http://127.0.0.1:8765` en otra terminal.

## 5.4 Contenedor

La imagen del `Dockerfile` se construyó el 13 de noviembre de 2026 con Docker 29.9.3 (Python 3.12.16 dentro de la imagen, Flask 3.1.3, Waitress 3.0.2 y TinyDB 4.9.0). Dentro del contenedor, `python -m unittest discover -s tests` aprobó 86 de 86 casos. Con el contenedor publicado en `127.0.0.1:8765` y el volumen `nuam-datos`, `prueba_humo_docker.py` comprobó seis puntos: el ingreso sin token CSRF se rechaza, el supervisor ingresa con token, el catálogo inicial es visible, el supervisor agrega un instrumento, el operador no puede hacerlo y el instrumento agregado sigue en la base después de `docker restart`. La aplicación corre con el usuario sin privilegios `nuam`. Los registros están en `evidencias/docker_20261113`.

En el equipo donde se construyó, la red pasa por un proxy con certificado propio. Para descargar las dependencias, la construcción entregó ese certificado a pip como secreto de construcción (`--secret`), que no queda en la imagen, y usó `--network host`. En un equipo con acceso directo a internet basta `docker build -t nuam-mantenedor:1.2 .`.

## 5.5 Uso de IA

Las versiones 1.1, 1.1.1, 1.2 y 1.2.1 se prepararon con apoyo de un asistente de inteligencia artificial generativa: corrección de D3, registro operativo, permiso configurable de factores, modo WAL, prueba de estrés, reglas DEMO-2 y DEMO-3, verificación del contenedor, guías de colaboración y de la sesión de usabilidad, documentación y ejecución de las pruebas. Las reglas DEMO-2 y DEMO-3 las definió el equipo para la demostración, con autorización del docente para completar las definiciones que faltaban. Los resultados registrados provienen de ejecuciones reales en el entorno indicado en cada informe. El equipo debe revisar el código y poder explicar sus decisiones; la validación docente se confirma por separado.
