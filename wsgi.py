"""Punto de entrada WSGI opcional para servir el prototipo con Waitress.

Uso local (solo equipo propio):
    waitress-serve --listen=127.0.0.1:8765 wsgi:app

NUAM_DATA_DIR permite ubicar la base, la clave local y los registros fuera
de la carpeta del código. Sin la variable se usa ./data, igual que app.py.
"""
import os

from app import create_app

app = create_app(os.environ.get("NUAM_DATA_DIR") or None)
