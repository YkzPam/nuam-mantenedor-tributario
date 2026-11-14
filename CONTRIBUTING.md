# Guía de trabajo del equipo

Proyecto Integrado TIHI43, Grupo 4: mantenedor de calificaciones tributarias para el caso NUAM.

## 1. Responsables por componente

La distribución proviene de la planificación y el diseño de la Unidad 2. Cada integrante responde por sus componentes, pero cualquier cambio lo revisa un integrante distinto de su autor.

| Integrante | Rol en Scrum | Componentes del paquete |
|---|---|---|
| Benjamín Concha | Orden del backlog y decisiones de producto | `domain.py` (regla DEMO-1), tabla `evento_auditoria` y cadena HMAC, recorrido de demostración |
| María Jesús Erices | Facilitación de Scrum y revisión de calidad | `templates/`, `static/`, validaciones de `domain.py`, carpeta `tests/` |
| Pablo Doussang | Desarrollo e integración de datos | `schema.sql`, rutas de `app.py`, `documentrepo.py`, permisos por rol y corredor |

### 1.1 Aportes en la Unidad 3

Según lo informado por el equipo el 14 de noviembre de 2026:

| Integrante | Aporte en la Unidad 3 |
|---|---|
| Benjamín Concha | Orden del backlog, regla DEMO-1 (conversión de montos a factores) y bitácora de auditoría |
| Pablo Doussang | Diagramas del proyecto y pruebas |
| María Jesús Erices | Redacción de los documentos de la entrega y presentación |

Los aportes de Pablo y María Jesús se hicieron fuera del repositorio. Por indicación del docente, la integración en el repositorio y la publicación en DreamShaper quedaron a cargo de un integrante, que registra en esta guía y en la documentación los aportes del resto; por eso los commits se registran desde una sola cuenta. La sección 5 describe cómo cada integrante puede trabajar con su propia cuenta si el equipo lo decide más adelante. El 14 de noviembre de 2026, según lo informado por el integrador, el docente confirmó al equipo que está de acuerdo con esta forma de trabajo: un integrante integra y publica, y la guía registra los aportes de los demás.

### 1.2 Revisión cruzada sin cuentas propias

Mientras Pablo y María Jesús no dispongan de computador para trabajar en GitHub, el paso 6 de la sección 2 se aplica fuera del repositorio con el siguiente procedimiento acordado:

1. El integrador prepara el cambio, ejecuta `python run_all_tests.py` y comparte con el equipo el material que se debe revisar: documento, diagrama o reporte de pruebas.
2. Pablo revisa lo relacionado con diagramas y casos de prueba. María Jesús revisa la redacción de los documentos y el material de la presentación. Ambos envían sus observaciones al integrador por el canal del equipo.
3. El integrador aplica las observaciones, repite las pruebas e integra el cambio en `main` con un commit que describe qué cambió.
4. La publicación en DreamShaper se hace después de que GitHub Actions aprueba el cambio.

Como estas revisiones no pasan por un pull request, el historial de GitHub no las registra. La sección 5 se mantiene como procedimiento para cuando cada integrante trabaje con su propia cuenta.

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
