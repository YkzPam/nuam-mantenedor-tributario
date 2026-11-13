# Guía de trabajo del equipo

Proyecto Integrado TIHI43, Grupo 4: mantenedor de calificaciones tributarias para el caso NUAM.

## 1. Responsables por componente

La distribución proviene de la planificación y el diseño de la Unidad 2. Cada integrante responde por sus componentes, pero cualquier cambio lo revisa un integrante distinto de su autor.

| Integrante | Rol en Scrum | Componentes del paquete |
|---|---|---|
| Benjamín Concha | Orden del backlog y decisiones de producto | `domain.py` (regla DEMO-1), tabla `evento_auditoria` y cadena HMAC, recorrido de demostración |
| María Jesús Erices | Facilitación de Scrum y revisión de calidad | `templates/`, `static/`, validaciones de `domain.py`, carpeta `tests/` |
| Pablo Doussang | Desarrollo e integración de datos | `schema.sql`, rutas de `app.py`, `documentrepo.py`, permisos por rol y corredor |

## 2. Flujo de un cambio

1. Registrar el cambio en el backlog con su origen: historia de usuario (HU01 a HU10), discrepancia del informe de pruebas (D1 a D7) o solicitud del docente.
2. Trabajar en una rama propia con nombre descriptivo, por ejemplo `correccion/d3-pattern-instrumento`.
3. Escribir o ajustar primero la prueba que demuestra el cambio. Las suites viven en `tests/` y cada caso lleva su identificador en la primera línea del docstring (`U`, `I`, `S`, `P`, `CP`, `UI`, `V`).
4. Ejecutar `python run_all_tests.py`. No se integra un cambio con fallas ni errores.
5. Si el cambio toca rendimiento, concurrencia o cargas, ejecutar también `python pruebas_estres.py` y adjuntar el informe que deja en `evidencias/`.
6. Solicitar la revisión a otro integrante. Quien revisa comprueba la prueba nueva, el perfil y corredor afectados y que no se registren secretos.
7. Actualizar `CHANGELOG.md`, `INICIO_UNIDAD3.md` si cambia la operación, y regenerar `MANIFIESTO_SHA256.json` antes de empaquetar.

## 3. Estándares de código

- Mínimo privilegio: toda ruta declara los perfiles permitidos con `need_user` y verifica el corredor del objeto.
- Consultas SQL solo con parámetros; nunca con texto concatenado del usuario.
- Calificación y evento de auditoría en la misma transacción (`BEGIN IMMEDIATE`). La base trabaja en modo WAL; no cambiarlo sin repetir `pruebas_estres.py`.
- Mutaciones con token CSRF. Mensajes de error sin rutas internas, SQL ni nombres de tablas.
- El registro operativo (`data/logs/operacion.log`) guarda método, ruta declarada, estado, duración y perfil. No se agregan cuerpos de solicitud, parámetros de búsqueda, cookies, tokens ni contraseñas.
- Dependencias con versión exacta en `requirements-lock.txt` y `requirements-servidor.txt`.
- Solo datos ficticios. Ningún archivo de `data/` ni de `evidencias/` se sube al repositorio (`.gitignore`).

## 4. Definición de terminado

Una tarea está terminada cuando cumple su historia de usuario, respeta perfil y corredor, conserva los datos y eventos exigidos, supera sus pruebas y deja evidencia. Una regla que NUAM no ha definido se mantiene marcada como pendiente aunque su demostración funcione.

## 5. Trabajo en GitHub con cuentas propias

Cada integrante trabaja con su propia cuenta de GitHub, para que el historial muestre quién hizo y quién revisó cada cambio.

1. Quien administra el repositorio agrega al integrante en Settings → Collaborators con permiso Write. El integrante acepta la invitación que le llega por correo.
2. El integrante clona el repositorio o lo abre en GitHub Desktop y crea una rama propia, como indica la sección 2.
3. Hace el cambio que le corresponde, con un commit que describa qué cambió y por qué, y lo sube a su rama.
4. Abre un pull request hacia `main`. La plantilla del pull request pide el origen del cambio, las pruebas ejecutadas y quién revisa.
5. Otro integrante revisa el pull request en la pestaña Files changed, deja sus observaciones y lo aprueba con Review changes → Approve. Solo después se integra.

GitHub Actions ejecuta las pruebas en Windows y Ubuntu en cada pull request. Si falla, el cambio no se integra hasta corregirlo.
