# 5. Verificación del paquete

## 5.1 Integridad de los archivos

El paquete entregado en DreamShaper es `NUAM_Unidad_3_Implementacion_v1.1.zip`, con huella SHA-256 `18cd606218ec3154b050fde109b5e551a8bf42e3201524a8fab5c1ed2d5d5c43`. `MANIFIESTO_SHA256.json` registra el tamaño y la huella de cada archivo de ese paquete e indica los que cambiaron respecto de la versión 1.0. En PowerShell, la huella de un archivo se obtiene con:

```powershell
Get-FileHash .\app.py -Algorithm SHA256
```

El README, la carpeta `docs/`, los accesos `.cmd`, `.gitattributes` y el flujo de GitHub Actions existen solo en el repositorio y no forman parte del manifiesto.

## 5.2 Pruebas

```powershell
verificar.cmd
```

El acceso prepara el entorno si falta y ejecuta `run_all_tests.py`. El resultado esperado es `"tests": 68, "passed": 68, "failed": 0, "errors": 0`, con un informe nuevo en `evidencias/`.

## 5.3 Estrés y servidor WSGI

```powershell
.\.venv\Scripts\python.exe pruebas_estres.py --segundos 60
.\.venv\Scripts\python.exe -m pip install -r requirements-servidor.txt
.\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8765 --threads=8 wsgi:app
```

Para medir por HTTP, iniciar Waitress con `NUAM_DATA_DIR` apuntando a una carpeta desechable y ejecutar `pruebas_estres.py --url http://127.0.0.1:8765` en otra terminal.

## 5.4 Uso de IA

La versión 1.1 se preparó con apoyo de un asistente de inteligencia artificial generativa: corrección de D3, registro operativo, permiso configurable de factores, modo WAL, prueba de estrés, documentación y ejecución de las pruebas. Los resultados registrados provienen de ejecuciones reales en el entorno indicado en cada informe. El equipo debe revisar el código y poder explicar sus decisiones; la validación docente se confirma por separado.
