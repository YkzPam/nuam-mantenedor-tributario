# 1. Arquitectura y datos

## 1.1 Componentes

| Archivo | Responsabilidad |
| --- | --- |
| `app.py` | Aplicación Flask creada con `create_app`: rutas, sesiones, token CSRF, permisos por rol y corredor, cargas, catálogo de instrumentos (DEMO-2), prioridad de la Bolsa (DEMO-3), bitácora y registro operativo |
| `domain.py` | Validación de campos, llave provisional, columnas de los CSV y regla ilustrativa DEMO-1 con `Decimal` y redondeo `HALF_UP` a seis decimales |
| `documentrepo.py` | Reportes de carga en TinyDB, con verificación de corredor y huella SHA-256 |
| `schema.sql` | Esquema SQLite 2: once tablas, índices, restricciones y disparadores |
| `templates/`, `static/` | Interfaz web de una sola página con cinco módulos: consulta y registros, cargas masivas, catálogo de instrumentos, conversión ilustrativa y bitácora |
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
| `instrumento` | Catálogo por mercado: código, inscripción, estado habilitado y versión (DEMO-2, desde la versión 1.2) |
| `calificacion` | Mercado, período, instrumento, calificación, monto, base, factor, origen (`manual`, `DJ1948-DEMO`, `factores-DEMO` o `bolsa-DEMO`), estado y versión |
| `carga` | Lote de carga con tipo, estado, totales y token de confirmación |
| `archivo` | Original y reporte de cada carga con nombre interno aleatorio y huella SHA-256 |
| `carga_fila` | Datos y errores de cada fila prevalidada |
| `evento_auditoria` | Bitácora con valores anteriores y nuevos, encadenada con HMAC |

`calificacion.instrumento` no es una llave foránea hacia `instrumento`, porque un no inscrito puede registrarse sin figurar en el catálogo; la relación se controla en cada escritura (sección 1.3). Las entidades maestras siguen la tercera forma normal. Dos datos derivados se guardan a propósito: el factor, porque registra el resultado de una versión de la regla, y los totales de cada carga, para no recorrer todas sus filas.

## 1.3 Restricciones e índices

| Objeto | Función |
| --- | --- |
| Llaves foráneas (`PRAGMA foreign_keys = ON`) | Impiden registros que apunten a corredores, usuarios o reglas inexistentes |
| Restricciones `CHECK` | Limitan mercado, origen, estado de lote, perfil, inscripción, estado del catálogo, JSON válido y largo de las huellas |
| `UNIQUE(mercado, codigo)` en `instrumento` | Un instrumento por código en cada mercado |
| Condición DEMO-2 en `INSERT` y `UPDATE` de `calificacion` | La escritura incluye la consulta al catálogo en la misma sentencia (`INSERT ... SELECT ... WHERE` y `UPDATE ... WHERE`): un inscrito fuera del catálogo o un instrumento deshabilitado o con inscripción distinta no se guarda, aunque el catálogo cambie durante la operación. La baja lógica no la evalúa. Se eligió en lugar de disparadores después de la prueba de estrés |
| `uq_calificacion_provisional` | Índice único parcial: una sola calificación activa por llave provisional |
| `ix_calificacion_busqueda` | Sigue el orden de los filtros de la consulta: corredor, estado, período y mercado |
| `ix_logout_session_hash` | Acelera la comprobación de que una sesión cerrada no vuelva a usarse |
| `auditoria_no_update`, `auditoria_no_delete` | Hacen la bitácora de solo adición |
| Columna `version` | Control optimista: una edición desactualizada recibe HTTP 409 |
| Modo WAL | Desde la versión 1.1, consultas y guardados no se bloquean entre sí; se mantiene un solo escritor |
| `PRAGMA user_version = 2` | Identifica el esquema. Una base anterior se respalda completa en `data/respaldo_v1_<fecha>/` antes de crear la nueva, porque SQLite no permite cambiar restricciones `CHECK` con `ALTER TABLE` |

## 1.4 Rutas de la API

| Ruta | Uso |
| --- | --- |
| `/api/me`, `/api/login`, `/api/logout` | Sesión y token CSRF |
| `/api/ratings`, `/api/ratings/<id>` | Consulta, alta, modificación y baja lógica |
| `/api/factor/preview` | Conversión ilustrativa de monto a factor |
| `/api/batches/preview`, `/api/batches/<id>/confirm`, `/api/batches` | Prevalidación, confirmación y listado de cargas |
| `/api/documents`, `/api/documents/<id>`, `/api/files/<id>` | Reportes de TinyDB y archivos privados |
| `/api/template/<tipo>` | Plantillas CSV de montos y factores; la de Bolsa solo para el supervisor |
| `/api/instruments`, `/api/instruments/<id>` | Consulta del catálogo (operador y supervisor); alta, deshabilitación y habilitación (solo supervisor) |
| `/api/audit` | Bitácora del ámbito del usuario con verificación de la cadena |
| `/api/users`, `/api/users/<id>` | Gestión de perfiles y corredores (solo administrador) |

## 1.5 Reglas de negocio de demostración

| Regla | Contenido | Origen |
| --- | --- | --- |
| DEMO-1 | Factor = monto / base, seis decimales, redondeo `HALF_UP`, entre 0 y 1 | Equipo, desde la versión 1.0 |
| DEMO-2 | Un inscrito debe figurar habilitado en el catálogo del mercado; un no inscrito fuera del catálogo se admite y, si figura, debe coincidir y estar habilitado | Equipo, versión 1.2 |
| DEMO-3 | El archivo `bolsa-DEMO`, cargado solo por el supervisor, reemplaza el registro del corredor con la misma llave; la bitácora guarda los valores anteriores y el operador no puede cambiar ni desactivar ese registro | Equipo, versión 1.2 |

Las tres reglas son de demostración y quedan pendientes de validación de NUAM. Las dos nuevas cierran la discrepancia D7 de la versión 1.1, que dejaba ambas definiciones abiertas.
