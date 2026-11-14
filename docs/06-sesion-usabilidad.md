# 6. Sesión de usabilidad con personas

El plan de pruebas de la Unidad 2 definió tres elementos de usabilidad (P-UX01, P-UX02 y P-UX05) con perfiles simulados, y el informe de pruebas los registra como simulación académica (discrepancias D1 y D2). Esta guía sirve para repetirlos con personas reales. Mientras la sesión no se haga, esos tres elementos siguen en simulación; no se deben completar los resultados sin haber realizado la sesión.

## 6.1 Preparación

- Participantes: dos o tres personas que no hayan desarrollado el prototipo, por ejemplo compañeros de otra sección o de otro grupo. Se identifican como P1, P2 y P3; no se registran nombres, RUT ni datos de contacto.
- Duración: 10 a 15 minutos por persona.
- Equipo: el paquete instalado según `INICIO_UNIDAD3.md`. Cada participante empieza con una base nueva, para que todos vean los mismos datos. Entre una persona y otra se detiene la aplicación con Ctrl+C, se cambia el nombre de la carpeta `data` (por ejemplo, a `data_sesion_P1`) y se vuelve a abrir con `iniciar.cmd`, que crea una carpeta `data` nueva con los datos ficticios iniciales. Las carpetas `data_sesion_*` no se suben al repositorio ni se adjuntan.

- Roles del equipo: una persona modera y lee las tareas; otra observa y llena `docs/plantilla_sesion_usabilidad.csv`. Quien modera no explica la interfaz ni indica dónde hacer clic. Si el participante pide ayuda, se le da y la tarea queda como completada con ayuda.

## 6.2 Tareas

Se leen en este orden. Contraseña de todas las cuentas: `Demo2026!`.

| Tarea | Elemento del plan | Instrucción para el participante | Se considera completada sin ayuda si |
|---|---|---|---|
| T1 | P-UX01 | Inicia sesión como `operador_a` y busca las calificaciones del instrumento DEMO-ALFA. | Llega al resultado de la búsqueda |
| T2 | P-UX01 | Crea una calificación: mercado SCL, período 2026-10, instrumento DEMO-BETA, inscrito, calificación "Tributaria demo", modo monto, monto 300 y base 1000. | La calificación aparece guardada |
| T3 | P-UX01 | Modifica la calificación que acabas de crear (monto 350) y después desactívala. | Ambos cambios quedan guardados |
| T4 | P-UX02 | En Cargas masivas, prevalida `ejemplos/03_campos_incompletos.csv` y explica con tus palabras qué fila falla y por qué. | Identifica la fila y el motivo correctos |
| T5 | P-UX01 | Prevalida y confirma `ejemplos/01_montos_valido.csv`. | El lote queda confirmado |

Con tres participantes son 15 tareas, la misma cantidad que la simulación del 7 de octubre. El criterio del plan es un 90 % de tareas completadas sin ayuda: 14 de 15 con tres personas, o 9 de 10 con dos.

## 6.3 Preguntas finales (P-UX05)

1. Del 1 (muy difícil) al 5 (muy fácil), ¿qué tan fácil fue usar el sistema?
2. ¿Qué fue lo más confuso?
3. ¿Qué cambiarías primero?

Las respuestas se anotan en la columna `comentario` de la fila `final` de cada participante. Si la sesión deja un cambio en la interfaz, se corrige con su prueba, como indica `CONTRIBUTING.md`, y se repite la tarea afectada con otra persona: esa es la segunda revisión del elemento P-UX05.

## 6.4 Registro

Se copia `docs/plantilla_sesion_usabilidad.csv` a `evidencias/usabilidad_<fecha>/resultados.csv` y se llena una fila por tarea y participante. Columnas:

| Columna | Valor |
|---|---|
| `participante` | P1, P2 o P3 |
| `fecha` | AAAA-MM-DD |
| `tarea` | T1 a T5, o `final` para las preguntas |
| `completada_sin_ayuda` | `si` o `no` |
| `tiempo_s` | Segundos aproximados desde que se lee la tarea |
| `errores` | Cantidad de intentos fallidos o caminos equivocados |
| `interpreto_mensaje` | Solo en T4: `si` o `no` |
| `facilidad_1_5` | Solo en la fila `final` |
| `comentario` | Lo que dijo o hizo la persona, en palabras simples |

Con el archivo lleno, el informe de pruebas cambia el estado de P-UX01, P-UX02 y P-UX05 de "Simulación" al resultado real, y D1 y D2 se actualizan con lo observado, sea favorable o no.

## 6.5 Simulación del 14 de noviembre

No hubo personas disponibles para esta sesión. Con autorización del docente, el protocolo se aplicó a tres perfiles ficticios sobre la versión 1.2.2: una operadora con experiencia, un analista recién incorporado y un operador que usa el celular a 360 px. El resultado fue 14 de 15 tareas sin ayuda (93,3 %); los tres perfiles interpretaron el error de T4 y la facilidad promedio fue 4,0 sobre 5. La tarea que requirió ayuda fue T3 en el celular, por el problema H-05 de la evaluación heurística. Los datos, rotulados como ficticios, están en `evidencias/usabilidad_simulada_20261114`. Esta simulación no reemplaza la sesión con personas: si se realiza, sus resultados se registran aparte y prevalecen.
