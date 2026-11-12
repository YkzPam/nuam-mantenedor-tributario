# Pruebas del paquete de la Unidad 3 (v1.1)

Fecha UTC: 2026-11-12T01:45:42.574940+00:00

Total real: 68/68 aprobadas, 0 fallas, 0 errores.

| Suite | Casos | Aprobados | Fallas | Errores |
|---|---:|---:|---:|---:|
| test_demo | 40 | 40 | 0 | 0 |
| test_ui_revision | 8 | 8 | 0 | 0 |
| test_complementarias | 10 | 10 | 0 | 0 |
| test_v11 | 10 | 10 | 0 | 0 |

## Correcciones verificadas

Ownership de archivos registrado antes de escribir; rollback de preview limpia todos los archivos creados.
Logout persiste SHA-256 del identificador aleatorio de sesión en evento de auditoría; la cookie anterior se rechaza incluso tras reiniciar con misma clave/base.
Índice parcial para hashes revocados sin tabla ni columna nueva; errores de almacenamiento controlados con 503 sin publicar rutas/SQL.
Los campos textuales obligatorios rechazan valores nulos, booleanos, colecciones y tipos incompatibles sin convertirlos a texto.
La confirmación exitosa sustituye el estado pendiente del lote visible, conserva el conteo confirmado y deshabilita una nueva confirmación; una respuesta anterior no sobrescribe la previsualización de otro lote.
v1.1: el atributo pattern del instrumento escapa el guion y vuelve a ser válido en Chrome (D3).
v1.1: registro operativo en data/logs/operacion.log con método, ruta declarada, estado, duración y perfil, sin cuerpo, consulta ni credenciales.
v1.1: NUAM_ROLES_FACTOR_MANUAL permite limitar el ingreso manual de factores; sin la variable rige la matriz de la Unidad 2.
v1.1: wsgi.py para servir con Waitress e ícono embebido que evita la solicitud 404 a /favicon.ico.
v1.1: SQLite en modo WAL; con 100 clientes en proceso el P95 de guardado bajó de 6,97 s con 31 respuestas 503 a 2,20 s sin 5xx (pruebas_estres.py).

## Casos complementarios y de regresión v1.1

| Caso | Resultado | Comprobación |
|---|---|---|
| test_CP01_twenty_concurrent_saves | passed | PLAN-R01: veinte guardados concurrentes, P95 y persistencia/auditoría. |
| test_CP02_preview_file_failure_cleans_every_created_file | passed | PLAN-I02: falla después del segundo archivo, sin SQL/documento/archivos huérfanos. |
| test_CP03_preview_document_failure_rolls_back_all_stores | passed | PLAN-I02: falla TinyDB tras escribir; revierte SQL, archivos y documento derivado. |
| test_CP04_confirmation_failure_after_first_insert_is_atomic | passed | PLAN-I02: falla en segunda fila al confirmar, sin calificación/evento parcial; reintento. |
| test_CP05_postcommit_document_failure_is_recoverable_without_duplicate | passed | PLAN-I02: falla documental posterior a commit conserva verdad SQL; reintento idempotente. |
| test_CP06_crud_audit_failure_rolls_back_insert_update_and_soft_delete | passed | PLAN-I03: falla de auditoría después de INSERT/UPDATE/baja revierte operación. |
| test_CP07_required_and_calculation_failure_have_no_business_mutation | passed | PLAN-F02/PLAN-I03: obligatorio vacío y cálculo inválido señalan error sin escritura. |
| test_CP08_csrf_all_mutations_missing_invalid_valid_and_audit_fields | passed | PLAN-S06/PLAN-F05: nueve familias CSRF y eventos de operaciones con todos sus campos. |
| test_CP09_login_privacy_logout_and_old_cookie_replay | passed | PLAN-S02: error uniforme y bitácora privada; cookie previa al logout no reutilizable. |
| test_CP10_five_supplied_csv_examples | passed | PLAN-F03: cinco archivos de ejemplo por API, errores explicados y rechazo completo. |
| test_V01_instrument_pattern_valid_and_equivalent | passed | V01 | regresión D3 | pattern con guion escapado y misma aceptación que el servidor |
| test_V02_favicon_declared_without_extra_request | passed | V02 | regresión | ícono embebido evita la solicitud 404 a /favicon.ico |
| test_V03_operation_log_metadata_only | passed | V03 | registro operativo | líneas JSON con método, ruta, estado, duración y perfil |
| test_V04_rejected_requests_are_logged | passed | V04 | registro operativo | CSRF rechazado y ruta inexistente quedan registrados |
| test_V05_factor_roles_from_environment | passed | V05 | configuración | NUAM_ROLES_FACTOR_MANUAL respeta la matriz y rechaza perfiles ajenos |
| test_V06_factor_restricted_profile_denied_and_audited | passed | V06 | permisos | perfil sin autorización no ingresa factores; monto sigue disponible |
| test_V07_factor_batch_denied_for_restricted_profile | passed | V07 | permisos | carga factores-DEMO rechazada antes de crear lote o archivos |
| test_V08_wsgi_entrypoint_uses_data_dir | passed | V08 | entorno | wsgi.py expone la aplicación y respeta NUAM_DATA_DIR |
| test_V09_operation_log_rotation_keeps_three_backups | passed | V09 | registro operativo | rotación por tamaño con tres archivos anteriores como máximo |
| test_V10_sqlite_wal_enabled | passed | V10 | optimización | SQLite en modo WAL con llaves foráneas activas en cada conexión |

## Límites de la evidencia

Ejecución técnica local con bases/archivos temporales. No modifica base visible, fuente ZIP ni Downloads. No prueba infraestructura NUAM, dispositivos físicos ni acciones/comentarios humanos. Fallos intermedios se inyectan deliberadamente.

Las mediciones y detalles de cada caso se conservan en resultados_corregidos.json. La suite de 40 casos conserva su P01 de consultas; CP01 agrega 20 escrituras simultáneas medidas separadamente. La prueba de estrés sostenida se ejecuta aparte con pruebas_estres.py.
