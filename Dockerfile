# Imagen opcional para ejecutar el prototipo con Waitress.
# Estado: redactada y revisada, no construida (el equipo de prueba no tenía el servicio de Docker).
# Los mismos pasos (Python 3.12, ambos archivos de dependencias, wsgi:app y NUAM_DATA_DIR) sí se
# ejecutaron fuera de un contenedor; ver INICIO_UNIDAD3.md, sección 5.
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
#   docker run --rm -p 127.0.0.1:8765:8765 -v nuam-datos:/datos nuam-mantenedor:1.1
CMD ["waitress-serve", "--listen=0.0.0.0:8765", "--threads=8", "wsgi:app"]
