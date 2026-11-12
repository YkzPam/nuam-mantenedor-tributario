@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto dependencias
rem El acceso de Microsoft Store llamado "python" no es un Python instalado: se comprueba la version.
set "PYTHON_CMD="
where py >nul 2>nul && py -3.12 -c "import sys" >nul 2>nul && set "PYTHON_CMD=py -3.12"
if not defined PYTHON_CMD python -c "import sys; sys.exit(sys.version_info < (3, 12))" >nul 2>nul && set "PYTHON_CMD=python"
if not defined PYTHON_CMD goto sin_python
echo Creando el entorno virtual .venv...
%PYTHON_CMD% -m venv .venv
if errorlevel 1 goto sin_python
:dependencias
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -r requirements-lock.txt
if errorlevel 1 goto sin_dependencias
echo Preparacion terminada. Ejecutar iniciar.cmd para abrir la demostracion.
exit /b 0
:sin_python
echo Se necesita Python 3.12 instalado desde https://www.python.org/downloads/
echo Durante la instalacion marcar "Add python.exe to PATH" y luego ejecutar de nuevo este archivo.
if not defined CI pause
exit /b 1
:sin_dependencias
echo No se pudieron instalar las dependencias. Revisar la conexion a internet y ejecutar de nuevo.
if not defined CI pause
exit /b 1
