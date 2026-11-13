"""Capturas de la interfaz v1.2.1 para la evaluación heurística (Chrome sin cabeza).

Uso, desde la carpeta del paquete: python evidencias/heuristica_20261113/heuristica_capturas.py <carpeta_salida> [url_base]
Requiere playwright y Chrome en /usr/bin/google-chrome. La base de datos debe ser nueva, porque el recorrido crea registros.
Recorre los estados que revisa la evaluación: ingreso, consulta, formulario con errores y válido,
modificación, desactivación, cargas con error y válidas, conversión, bitácora, catálogo y vista móvil.
"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
BASE = sys.argv[2] if len(sys.argv) > 2 else "http://127.0.0.1:8766"
EXAMPLES = Path.cwd() / "ejemplos"  # ejecutar desde la carpeta del paquete con la demo iniciada
log = []


def shot(page, name, nota):
    page.screenshot(path=str(OUT / name), full_page=True)
    log.append(dict(captura=name, estado=nota, mensaje=page.locator("#message").inner_text() if page.locator("#message").count() else ""))


def login(page, user, password="Demo2026!"):
    page.goto(BASE + "/")
    page.fill("#login", user)
    page.fill("#password", password)
    page.click("#login-form button[type=submit]")


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path="/usr/bin/google-chrome", headless=True)
    ctx = browser.new_context(viewport={"width": 1366, "height": 900}, locale="es-CL")
    page = ctx.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))

    page.goto(BASE + "/")
    shot(page, "01_ingreso.png", "Pantalla de ingreso")
    login(page, "operador_a", "clave-incorrecta")
    page.locator("#login-message").filter(has_text="Credenciales").wait_for()
    shot(page, "02_ingreso_error.png", "Contraseña incorrecta")

    login(page, "operador_a")
    page.wait_for_selector("#logout")
    page.locator("#rating-rows tr").first.wait_for()
    shot(page, "03_consulta_inicial.png", "Operador: consulta inicial")
    page.fill("#filter-query", "DEMO-ALFA")
    page.click("#search-form button[type=submit]")
    page.locator("#count").filter(has_text="1").wait_for()
    shot(page, "04_busqueda.png", "Búsqueda de DEMO-ALFA")
    page.click("#clear-filter")

    page.click("#new-rating")
    page.wait_for_selector("#edit-dialog[open]")
    page.click("#rating-form button[type=submit]")
    page.wait_for_timeout(500)
    shot(page, "05_formulario_vacio.png", "Formulario enviado sin datos")
    page.select_option("#rating-market", "SCL")
    page.fill("#rating-period", "2026-10")
    page.fill("#rating-instrument", "DEMO-BETA")
    page.fill("#rating-name", "Tributaria demo")
    page.select_option("#rating-registered", "1")
    page.select_option("#rating-mode", "monto")
    page.fill("#rating-amount", "300")
    page.fill("#rating-base", "1000")
    shot(page, "06_formulario_completo.png", "Formulario completo antes de guardar")
    page.click("#rating-form button[type=submit]")
    page.wait_for_selector("#edit-dialog", state="hidden")
    page.locator("#rating-rows tr", has_text="DEMO-BETA").first.wait_for()
    shot(page, "07_guardado.png", "Calificación guardada")

    row = page.locator("#rating-rows tr", has_text="DEMO-BETA").first
    row.get_by_role("button", name="Modificar").click()
    page.wait_for_selector("#edit-dialog[open]")
    shot(page, "08_modificar.png", "Formulario de modificación")
    page.locator("#edit-dialog .close-dialog").first.click()
    row.get_by_role("button", name="Desactivar").click()
    page.wait_for_selector("#delete-dialog[open]")
    shot(page, "09_desactivar.png", "Confirmación de desactivación")
    page.click("#cancel-delete")

    page.click("button[data-view=carga]")
    page.set_input_files("#batch-file", str(EXAMPLES / "03_campos_incompletos.csv"))
    page.click("#upload-form button[type=submit]")
    page.wait_for_selector("#preview:not([hidden])")
    page.locator("#preview-rows tr").first.wait_for()
    shot(page, "10_carga_con_errores.png", "Prevalidación de 03_campos_incompletos.csv")
    page.set_input_files("#batch-file", str(EXAMPLES / "01_montos_valido.csv"))
    page.click("#upload-form button[type=submit]")
    page.wait_for_timeout(1500)
    shot(page, "11_carga_valida.png", "Prevalidación de 01_montos_valido.csv")
    if page.locator("#confirm-batch").is_enabled():
        page.click("#confirm-batch")
        page.locator("#preview-count", has_text="confirmada").wait_for()
        shot(page, "12_carga_confirmada.png", "Lote confirmado")

    page.click("button[data-view=factores]")
    page.fill("#factor-amount", "250")
    page.fill("#factor-base", "1000")
    page.click("#factor-form button[type=submit]")
    page.wait_for_timeout(800)
    shot(page, "13_conversion.png", "Conversión ilustrativa DEMO-1")

    page.click("button[data-view=auditoria]")
    page.wait_for_timeout(1200)
    shot(page, "14_bitacora.png", "Bitácora e integridad")
    page.click("#logout")

    login(page, "supervisor")
    page.wait_for_selector("#logout")
    page.click("button[data-view=catalogo]")
    page.locator("#catalog-rows tr").first.wait_for()
    shot(page, "15_catalogo_supervisor.png", "Supervisor: catálogo de instrumentos")
    page.click("#logout")

    m = browser.new_context(viewport={"width": 360, "height": 780}, locale="es-CL", is_mobile=True)
    mp = m.new_page()
    login(mp, "operador_a")
    mp.wait_for_selector("#logout")
    mp.locator("#rating-rows tr").first.wait_for()
    shot(mp, "16_movil_consulta.png", "Consulta a 360 px")
    mp.click("#new-rating")
    mp.wait_for_selector("#edit-dialog[open]")
    shot(mp, "17_movil_formulario.png", "Formulario a 360 px")

    log.append(dict(errores_consola=errors))
    (OUT / "recorrido.json").write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    browser.close()
print(json.dumps(log, ensure_ascii=False, indent=1))
