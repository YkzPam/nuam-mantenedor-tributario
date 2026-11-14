# 4. Correspondencia con la rúbrica de la Unidad 3

La tabla relaciona cada indicador con la evidencia del repositorio y de los documentos entregados en DreamShaper. Identifica dónde revisar cada punto; no reemplaza la evaluación del docente.

| Indicador | Puntos | Evidencia | Observación |
| --- | ---: | --- | --- |
| 3.1.1.1 Interfaces y necesidades del negocio | 5 | Diez historias de usuario implementadas (documento de asesoría, 6.2); catálogo y prioridad de la Bolsa desde la versión 1.2; `templates/`, `static/` | Reglas DEMO-2 y DEMO-3 pendientes de validación de NUAM |
| 3.1.1.2 Lineamientos estéticos y funcionales | 5 | Revisión en Chrome a 360, 768 y 1440 px y con teclado; UI01 a UI08; V01 | Evaluación heurística con diez heurísticas y siete hallazgos, todos corregidos ([07-evaluacion-heuristica.md](07-evaluacion-heuristica.md)); usabilidad con perfiles simulados; la sesión con personas sigue [06-sesion-usabilidad.md](06-sesion-usabilidad.md) |
| 3.1.2.3 Estructura de la base de datos | 5 | `schema.sql` (once tablas; catálogo de instrumentos); [01-arquitectura-y-datos.md](01-arquitectura-y-datos.md) | — |
| 3.1.2.4 Optimización y normalización | 5 | Tercera forma normal, índices, modo WAL y su medición en [03-pruebas-y-resultados.md](03-pruebas-y-resultados.md) | — |
| 3.1.3.5 Patrones de seguridad | 5 | [02-seguridad.md](02-seguridad.md); suites S, CP, V y W | — |
| 3.1.3.6 Colaboración en equipo | 5 | `CONTRIBUTING.md` (roles, aportes de cada integrante en la Unidad 3 y flujo con pull requests), plantilla de pull request, `CHANGELOG.md`, Anexo C del documento de asesoría | Los commits del repositorio se hicieron desde una sola cuenta; los aportes de Pablo y María Jesús se hicieron fuera del repositorio |
| 3.1.4.7 Configuración del entorno | 10 | `INICIO_UNIDAD3.md`, `preparar.cmd`, `iniciar.cmd`, `verificar.cmd`, `wsgi.py`, `Dockerfile`; imagen verificada en `evidencias/docker_20261113` | — |
| 3.1.4.8 Documentación de la implementación | 5 | Sección 7 del documento de asesoría, `INICIO_UNIDAD3.md`, `MANIFIESTO_SHA256.json` | — |
| 3.1.5.9 Cobertura del plan de pruebas | 10 | 26 elementos del plan; casos de borde (U03 a U09) y estrés (`pruebas_estres.py`); evaluación heurística en [07-evaluacion-heuristica.md](07-evaluacion-heuristica.md); guía de la sesión con personas y simulación del 14 de noviembre en [06-sesion-usabilidad.md](06-sesion-usabilidad.md) | Usabilidad con dos simulaciones autorizadas y evaluación heurística; la prueba con personas queda para el piloto |
| 3.1.5.10 Ejecución del protocolo | 10 | `run_all_tests.py`, `evidencias/`, GitHub Actions | — |
| 3.1.5.11 Validación de resultados | 10 | Informe de pruebas extendido, secciones 4 a 7 | — |
| 3.1.6.12 Discrepancias | 10 | D1 a D8 con causa y efecto | — |
| 3.1.6.13 Recomendaciones | 5 | Tabla de recomendaciones con indicador de cumplimiento | — |
| 3.1.6.14 Respuesta a preguntas | 5 | Presentación oral | No depende del repositorio |
| 3.1.6.15 Informe final | 5 | `docs/Propuesta_asesoria_NUAM_Grupo4.docx` | Formato Carta, márgenes de 2,5 cm, Calibri, títulos numerados y APA 7 |
