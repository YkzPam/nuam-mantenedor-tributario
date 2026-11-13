# Imagen opcional para ejecutar el prototipo con Waitress.
# Construida y verificada el 13 de noviembre de 2026 con Docker 29.9.3: 86 de 86 pruebas dentro
# del contenedor y prueba de humo con volumen persistente (evidencias/docker_20261113).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    NUAM_DATA_DIR=/datos

WORKDIR /app
COPY requirements-lock.txt requirements-servidor.txt ./
RUN pip install --no-cache-dir -r requirements-lock.txt -r requirements-servidor.txt

COPY . .
RUN useradd --create-home --uid 10001 nuam \
    && mkdir -p /datos \
    && chown nuam:nuam /datos
USER nuam
VOLUME ["/datos"]
EXPOSE 8765

# Dentro del contenedor escucha en todas sus interfaces; publicar solo en el loopback del equipo:
#   docker run --rm -p 127.0.0.1:8765:8765 -v nuam-datos:/datos nuam-mantenedor:1.2
CMD ["waitress-serve", "--listen=0.0.0.0:8765", "--threads=8", "wsgi:app"]
