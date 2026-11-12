@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (call preparar.cmd || exit /b 1)
".venv\Scripts\python.exe" run_all_tests.py
set "RESULTADO=%ERRORLEVEL%"
echo.
if "%RESULTADO%"=="0" echo Pruebas aprobadas. El informe quedo en la carpeta evidencias.
if not "%RESULTADO%"=="0" echo Hay pruebas con fallas o errores. Revisar el informe en la carpeta evidencias.
if not defined CI pause
exit /b %RESULTADO%
