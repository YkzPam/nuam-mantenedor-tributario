# 1. Arquitectura y datos

## 1.1 Componentes

| Archivo | Responsabilidad |
| --- | --- |
| `app.py` | Aplicación Flask creada con `create_app`: rutas, sesiones, token CSRF, permisos por rol y corredor, cargas, bitácora y registro operativo |
| `domain.py` | Validación de campos, llave provisional, columnas de los CSV y regla ilustrativa DEMO-1 con `Decimal` y redondeo `HALF_UP` a seis decimales |
| `documentrepo.py` | Reportes de carga en TinyDB, con verificación de corredor y huella SHA-256 |
| `schema.sql` | Esquema SQLite: diez tablas, índices, restricciones y disparadores |
| `templates/`, `static/` | Interfaz web de una sola página con cuatro módulos: consulta y registros, cargas masivas, conversión ilustrativa y bitácora |
| `wsgi.py` | Punto de entrada para servir la misma aplicación con Waitress |

SQLite es la fuente de verdad. TinyDB guarda el reporte completo de cada carga y SQLite registra su huella; si el documento no coincide, la aplicación responde con conflicto (HTTP 409).

## 1.2 Modelo relacional

| Tabla | Contenido |
| --- | --- |
| `rol` | Perfiles operador, supervisor y administrador |
| `corredor` | Corredores ficticios DEMO-A y DEMO-B |
| `usuario` | Cuentas con hash de contraseña, perfil, estado y versión |
| `usuario_corredor` | Asignación de corredores a cada cuenta |
| `regla_factor` | Versión de la regla de cálculo; la columna `aprobada_nuam` solo admite 0 |
| `calificacion` | Mercado, período, instrumento, calificación, monto, base, factor, origen, estado y versión |
| `carga` | Lote de carga con tipo, estado, totales y token de confirmación |
| `archivo` | Original y reporte de cada carga con nombre interno aleatorio y huella SHA-256 |
| `carga_fila` | Datos y errores de cada fila prevalidada |
| `evento_auditoria` | Bitácora con valores anteriores y nuevos, encadenada con HMAC |

Las entidades maestras siguen la tercera forma normal. Dos datos derivados se guardan a propósito: el factor, porque registra el resultado de una versión de la regla, y los totales de cada carga, para no recorrer todas sus filas.

## 1.3 Restricciones e índices

| Objeto | Función |
| --- | --- |
| Llaves foráneas (`PRAGMA foreign_keys = ON`) | Impiden registros que apunten a corredores, usuarios o reglas inexistentes |
| Restricciones `CHECK` | Limitan mercado, origen, estado de lote, perfil, JSON válido y largo de las huellas |
| `uq_calificacion_provisional` | Índice único parcial: una sola calificación activa por llave provisional |
| `ix_calificacion_busqueda` | Sigue el orden de los filtros de la consulta: corredor, estado, período y mercado |
| `ix_logout_session_hash` | Acelera la comprobación de que una sesión cerrada no vuelva a usarse |
| `auditoria_no_update`, `auditoria_no_delete` | Hacen la bitácora de solo adición |
| Columna `version` | Control optimista: una edición desactualizada recibe HTTP 409 |
| Modo WAL | Desde la versión 1.1, consultas y guardados no se bloquean entre sí; se mantiene un solo escritor |

## 1.4 Rutas de la API

| Ruta | Uso |
| --- | --- |
| `/api/me`, `/api/login`, `/api/logout` | Sesión y token CSRF |
| `/api/ratings`, `/api/ratings/<id>` | Consulta, alta, modificación y baja lógica |
| `/api/factor/preview` | Conversión ilustrativa de monto a factor |
| `/api/batches/preview`, `/api/batches/<id>/confirm`, `/api/batches` | Prevalidación, confirmación y listado de cargas |
| `/api/documents`, `/api/documents/<id>`, `/api/files/<id>` | Reportes de TinyDB y archivos privados |
| `/api/template/<tipo>` | Plantillas CSV de montos y factores |
| `/api/audit` | Bitácora del ámbito del usuario con verificación de la cadena |
| `/api/users`, `/api/users/<id>` | Gestión de perfiles y corredores (solo administrador) |
