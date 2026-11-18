# Recorrido de la versión 1.3 en Chrome — 18 de noviembre de 2026

Chrome sin cabeza (Playwright) contra `app.py` iniciado con una carpeta `data/` nueva. El script `recorrido_v13.py` ingresa con `operador_a`, `operador_b`, `supervisor` y `admin`, recorre consulta, creación, modificación, cargas 01, 03, 06 y 07, catálogo, conversión, bitácora y perfiles, y revisa el texto visible de cada pantalla en busca de "ficti", "demostraci", "ilustrativ", "demo" y "académic".

Resultado:

- Ninguna de esas palabras aparece en las pantallas revisadas.
- INS-ALFA muestra factor 0,250000 y origen Manual; la calificación nueva INS-BETA queda en 0,300000 y, al modificarla, en 0,350000.
- `03_campos_incompletos.csv` se rechaza completo (fila 2 sin período) y `01_montos_valido.csv` se confirma con 2 registros.
- `operador_b` no ve INS-ALFA.
- El archivo de Bolsa reemplaza INS-ALFA con 0,300000; `07_catalogo_rechazos.csv` se rechaza por la regla de catálogo.
- La bitácora informa "Integridad verificada: cadena HMAC y referencias anteriores correctas".
- Conversión: "Factor calculado: 0.250000 · regla CONV-1".
- Sin errores en la consola del navegador ni respuestas 5xx del servidor.

| Captura | Pantalla |
|---|---|
| `01_login.jpg` | Ingreso |
| `02_consulta.jpg` | Consulta de `operador_a` |
| `03_formulario.jpg` | Creación de una calificación |
| `04_detalle.jpg` | Detalle de la calificación |
| `05_carga.jpg` | Prevalidación rechazada |
| `07_catalogo.jpg` | Catálogo de instrumentos |
| `08_factores.jpg` | Conversión de montos |
| `09_bitacora.jpg` | Bitácora del supervisor |
| `10_prioridad.jpg` | INS-ALFA con prioridad Bolsa |
| `11_admin.jpg` | Perfiles y corredores |
| `12_movil.jpg` | Consulta a 390 px |
