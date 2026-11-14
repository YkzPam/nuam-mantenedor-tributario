# 7. Evaluación heurística de la interfaz

## 7.1 Método

El 13 de noviembre de 2026 se revisó la interfaz de la versión 1.2.1 con las diez heurísticas de usabilidad de Nielsen y su escala de severidad de 0 a 4: 0 no es un problema, 1 cosmético, 2 menor, 3 mayor y 4 catástrofe. El recorrido se hizo con Chrome sin cabeza contra el contenedor Docker, con una base nueva, a 1366 y a 360 píxeles de ancho. Abarcó el ingreso correcto y con error, la consulta, la búsqueda, el formulario vacío y completo, la modificación, la desactivación, una carga con errores, una carga válida confirmada, la conversión DEMO-1, la bitácora y el catálogo del supervisor. Las 17 capturas y el script que las generó están en `evidencias/heuristica_20261113/antes`.

La evaluación la hizo un solo evaluador: el asistente de IA declarado en `docs/05-verificacion.md`, a pedido del equipo. Nielsen advierte que las severidades asignadas por una sola persona son poco confiables y recomienda promediar las de varios evaluadores, por lo que conviene que cada integrante califique por su cuenta la tabla 7.3. La evaluación heurística no reemplaza la prueba con usuarios: los elementos P-UX01, P-UX02 y P-UX05 del plan siguen en simulación hasta realizar la sesión de `docs/06-sesion-usabilidad.md`.

## 7.2 Resultado por heurística

| Heurística | Lo que cumple la interfaz | Hallazgo |
|---|---|---|
| 1. Visibilidad del estado del sistema | Avisos después de guardar, cargar y confirmar; conteo de registros y páginas; estado de integridad de la bitácora | H-01, H-04 |
| 2. Relación con el mundo real | Rótulos en español del negocio: corredor, mercado, período, calificación, inscripción | H-03 |
| 3. Control y libertad del usuario | Cancelar y cerrar en cada diálogo; en la desactivación, Cancelar es la opción destacada; baja lógica, no borrado | — |
| 4. Consistencia y estándares | Mismos estilos para acciones principales y secundarias en todas las vistas; menú lateral fijo | H-02 |
| 5. Prevención de errores | Prevalidación antes de confirmar; rechazo completo de un lote con errores; confirmación de la desactivación; catálogo DEMO-2 | H-06 |
| 6. Reconocer antes que recordar | Lista de instrumentos del catálogo en el formulario y aviso "Catálogo: inscrito · habilitado"; filtros visibles | H-05 |
| 7. Flexibilidad y eficiencia | Filtros combinables, plantillas CSV y ejemplos de un clic | — |
| 8. Diseño estético y minimalista | Una tarea por vista, sin elementos decorativos | — |
| 9. Ayuda para reconocer y corregir errores | Motivo por fila en las cargas ("Período: completar con texto válido"); mensajes de API sin rutas ni SQL | H-07 |
| 10. Ayuda y documentación | Texto de cada regla DEMO junto al control que afecta; sección "Credenciales y límites de la demostración" en el ingreso | — |

## 7.3 Hallazgos

| Id | Pantalla | Problema | Heurística | Severidad | Estado |
|---|---|---|---|---:|---|
| H-01 | Todas las vistas | El aviso de la última acción (por ejemplo, "2 registro(s) incorporado(s)") seguía visible al cambiar a otra vista, como la Bitácora, donde no corresponde | 1 | 1 | Corregido en 1.2.2 |
| H-02 | Ingreso | El rótulo decía "Proyecto Integrado · Unidad 2" en la entrega de la Unidad 3 | 4 | 1 | Corregido en 1.2.2 |
| H-03 | Bitácora | Cada evento mostraba "Usuario 1 · Corredor 1" en vez del usuario y el corredor, y la entidad "calificacion" sin tilde | 2 | 2 | Corregido en 1.2.2 |
| H-04 | Formulario | En modo monto, el campo Factor directo está inactivo pero se veía igual que uno activo, con su valor de ejemplo | 1 | 1 | Corregido en 1.2.2 |
| H-05 | Consulta a 360 px | Las columnas Factor, Origen y Acciones quedan fuera de la pantalla; hay que desplazar la tabla hacia el lado sin una señal que lo indique | 6 | 2 | Corregido en 1.2.4 |
| H-06 | Formulario de creación | El formulario abre con valores de ejemplo (calificación, monto, base y factor); se podrían guardar sin revisarlos | 5 | 2 | Corregido en 1.2.4 |
| H-07 | Formulario enviado vacío | La validación nativa del navegador marca un campo a la vez, en el idioma del navegador ("Please fill out this field" en Chrome en inglés) | 9 | 1 | Corregido en 1.2.4 |

## 7.4 Correcciones y verificación

La versión 1.2.2 corrige H-01 a H-04. El aviso se oculta al cambiar de vista. La pantalla de ingreso indica la Unidad 3. La consulta de la bitácora agrega el usuario y el código del corredor con una unión de lectura, sin modificar la tabla de eventos ni su cadena HMAC, y la interfaz muestra "calificación" con tilde. Los campos inactivos usan fondo gris y borde discontinuo. Los casos W19 y W20 verifican estos cambios, y las cinco suites aprobaron 88 de 88 dentro del contenedor (`evidencias/ejecucion_completa_20261113_185008_912162`). Las capturas posteriores están en `evidencias/heuristica_20261113/despues`. Los cambios no tocan la escritura de calificaciones, por lo que la prueba de estrés de la versión 1.2 sigue vigente.

La versión 1.2.4 corrige H-05 a H-07. A 700 píxeles o menos, cada calificación se muestra como una tarjeta con sus datos rotulados y los botones Detalle, Modificar y Desactivar visibles, sin desplazamiento lateral. El formulario de creación abre vacío y los ejemplos quedan solo como texto de ayuda dentro de cada campo. La validación nativa del navegador se reemplazó por una propia que, al guardar, indica en español todos los campos pendientes de una vez, por ejemplo "Revisa estos campos: Período (falta completar), Monto ficticio (falta completar)", marca esos campos y lleva el foco al primero. Los casos W21 y W22 verifican estos cambios. Las cinco suites aprobaron 90 de 90 dentro de la imagen Docker 1.2.4 (`evidencias/ejecucion_completa_20261114_153652_447706`), y las capturas posteriores están en `evidencias/heuristica_20261113/despues_v1_2_4`. Con estas correcciones, los siete hallazgos de la evaluación quedan resueltos.

## 7.5 Referencias

- Nielsen, J. (1994). *10 usability heuristics for user interface design*. Nielsen Norman Group. https://www.nngroup.com/articles/ten-usability-heuristics/
- Nielsen, J. (1994). *Severity ratings for usability problems*. Nielsen Norman Group. https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/
