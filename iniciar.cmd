@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (call preparar.cmd || goto error)
".venv\Scripts\python.exe" -c "import flask, tinydb" >nul 2>nul || (call preparar.cmd || goto error)
echo.
echo Abrir http://127.0.0.1:8765 en el navegador de este equipo.
echo Usuarios ficticios: operador_a, operador_b, supervisor y admin. Clave: Demo2026!
echo Mantener esta ventana abierta mientras se usa la demostracion. Detener con Ctrl+C.
echo.
".venv\Scripts\python.exe" app.py
exit /b 0
:error
echo No se pudo iniciar la demostracion. Revisar el mensaje anterior.
pause
exit /b 1
