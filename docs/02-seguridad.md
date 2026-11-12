# 2. Seguridad del código

## 2.1 Controles implementados

| Riesgo | Control | Prueba |
| --- | --- | --- |
| Solicitudes falsificadas (CSRF) | Token aleatorio por sesión, comparado en tiempo constante; cookie `SameSite=Strict` | S02, CP08 |
| Inyección SQL | Consultas parametrizadas en todas las operaciones | S05 |
| Scripts maliciosos (XSS) | Validación de caracteres, inserción con `textContent` y política CSP sin scripts externos ni inline | S06, UI03 |
| Acceso fuera del ámbito | Autorización en el servidor por rol y por corredor en cada ruta | S03, S04, S10, S14 |
| Robo o reutilización de sesión | Cookie `HttpOnly`, vencimiento a los 30 minutos e invalidación al cerrar sesión | S12, CP09 |
| Adivinación de contraseñas | Hash PBKDF2, bloqueo temporal tras cinco intentos fallidos y mensaje uniforme | S13, CP09 |
| Archivos maliciosos | Solo CSV UTF-8, máximo 500 KB y 1.000 filas, nombre interno aleatorio y huella SHA-256 | U08, U09, S07, S08 |
| Alteración de la bitácora | Disparadores de solo adición y cadena HMAC verificable | S09 |
| Ingreso de factores por perfiles no autorizados | `NUAM_ROLES_FACTOR_MANUAL` validada al iniciar; el intento rechazado queda en la bitácora | V05, V06, V07 |
| Datos sensibles en registros | El registro operativo guarda ruta declarada, método, estado, duración y perfil, sin cuerpos, búsquedas, cookies ni credenciales | V03, V04 |
| Encuadre y fuga de origen | `X-Frame-Options DENY`, `X-Content-Type-Options nosniff`, `Referrer-Policy same-origin` y hosts de confianza limitados | Revisión de código |

Los controles siguen las recomendaciones de seguridad de Flask y la hoja de prevención de CSRF de OWASP, citadas en el documento de asesoría.

## 2.2 Límites conocidos

La cookie de sesión no tiene el atributo `Secure` porque la demostración funciona por HTTP en el mismo equipo. Antes de exponerla en una red se debe servir por HTTPS, activar `Secure` y agregar `Strict-Transport-Security`. Las contraseñas de las cuentas ficticias son públicas y no sirven para producción. La revisión de dependencias se hizo con una consulta fechada a la base OSV y debe repetirse en cada actualización.
