"""Recorrido de interfaz v1.2 con Chrome sin cabeza: catálogo (DEMO-2) y prioridad Bolsa (DEMO-3).

Script usado para generar esta carpeta. Requiere Playwright y Google Chrome, que no forman parte
de requirements-lock.txt, y una instancia de la aplicación con base nueva en 127.0.0.1:8766.
Uso: python recorrido_ui_v12.py <carpeta_salida>
"""
import json
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8766"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)
EXAMPLES = Path(__file__).resolve().parents[2] / "ejemplos"
log = []


def shot(page, name):
    page.screenshot(path=str(OUT / name), full_page=True)
    log.append(dict(captura=name))


def login(page, user):
    page.goto(BASE + "/")
    page.fill("#login", user)
    page.fill("#password", "Demo2026!")
    page.click("#login-form button[type=submit]")
    page.wait_for_selector("#logout")


with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get("CHROME", "/usr/bin/google-chrome"), headless=True)
    context = browser.new_context(viewport={"width": 1366, "height": 900}, locale="es-CL")
    page = context.new_page()
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))

    login(page, "supervisor")
    page.click("button[data-view=catalogo]")
    page.wait_for_selector("#catalog-rows tr")
    rows = page.locator("#catalog-rows tr").count()
    suspended = page.locator("#catalog-rows tr", has_text="DEMO-SUSPENDIDO").inner_text()
    page.select_option("#instrument-market", "SCL")
    page.fill("#instrument-code", "demo-gamma")
    page.select_option("#instrument-registered", "1")
    page.click("#instrument-form button[type=submit]")
    page.locator("#catalog-rows", has_text="DEMO-GAMMA").wait_for()
    log.append(dict(paso="catalogo_supervisor", filas_iniciales=rows, suspendido=suspended,
                    agregado=page.locator("#catalog-rows tr", has_text="DEMO-GAMMA").inner_text(), mensaje=page.inner_text("#message")))
    shot(page, "01_catalogo_supervisor.png")

    page.click("button[data-view=carga]")
    page.select_option("#batch-broker", "1")
    page.select_option("#batch-kind", "bolsa-DEMO")
    page.set_input_files("#batch-file", str(EXAMPLES / "06_bolsa_prioridad.csv"))
    page.click("#upload-form button[type=submit]")
    page.wait_for_selector("#preview:not([hidden])")
    page.locator("#preview-rows tr").first.wait_for()
    log.append(dict(paso="previsualizar_bolsa", conteo=page.inner_text("#preview-count"), fila=page.inner_text("#preview-rows")))
    shot(page, "02_bolsa_previsualizacion_reemplazo.png")
    page.click("#confirm-batch")
    page.locator("#preview-count", has_text="confirmada").wait_for()
    log.append(dict(paso="confirmar_bolsa", conteo=page.inner_text("#preview-count")))
    shot(page, "03_bolsa_confirmada.png")

    page.set_input_files("#batch-file", str(EXAMPLES / "07_catalogo_rechazos.csv"))
    page.select_option("#batch-kind", "DJ1948-DEMO")
    page.click("#upload-form button[type=submit]")
    page.locator("#preview-count", has_text="Rechazo total").wait_for()
    log.append(dict(paso="previsualizar_catalogo_rechazos", conteo=page.inner_text("#preview-count"), filas=page.inner_text("#preview-rows")))
    shot(page, "04_catalogo_rechazos.png")

    page.click("button[data-view=consulta]")
    page.select_option("#filter-origin", "bolsa-DEMO")
    page.click("#search-form button[type=submit]")
    page.locator("#count", has_text="1 registro(s)").wait_for()
    log.append(dict(paso="consulta_supervisor_bolsa", filas=page.inner_text("#rating-rows")))
    shot(page, "05_consulta_supervisor_bolsa.png")
    page.click("#logout")
    page.wait_for_selector("#login-form")

    login(page, "operador_a")
    page.locator("#rating-rows", has_text="Prioridad Bolsa").wait_for()
    row = page.locator("#rating-rows tr", has_text="Prioridad Bolsa")
    disabled = [row.locator("button", has_text=label).is_disabled() for label in ("Detalle", "Modificar", "Desactivar")]
    log.append(dict(paso="operador_botones_bolsa", detalle_deshabilitado=disabled[0], modificar_deshabilitado=disabled[1], desactivar_deshabilitado=disabled[2],
                    titulo=row.locator("button", has_text="Modificar").get_attribute("title")))
    shot(page, "06_operador_registro_bolsa.png")

    page.click("#new-rating")
    page.fill("#rating-instrument", "demo-beta")
    page.locator("#rating-instrument").dispatch_event("change")
    hint_known = page.inner_text("#catalog-hint")
    registered_known = page.input_value("#rating-registered")
    page.fill("#rating-instrument", "UI-V12-NUEVO")
    page.locator("#rating-instrument").dispatch_event("change")
    hint_new = page.inner_text("#catalog-hint")
    registered_new = page.input_value("#rating-registered")
    log.append(dict(paso="formulario_catalogo", conocido=hint_known, inscripcion_conocido=registered_known, nuevo=hint_new, inscripcion_nuevo=registered_new))
    shot(page, "07_formulario_sugerencia_catalogo.png")
    page.click("#rating-form button[type=submit]")
    page.locator("#edit-dialog").wait_for(state="hidden")
    page.click("button[data-view=catalogo]")
    page.fill("#catalog-query", "GAMMA")
    page.click("#catalog-form button[type=submit]")
    page.locator("#catalog-count", has_text="1 instrumento(s)").wait_for()
    log.append(dict(paso="catalogo_operador", filas=page.inner_text("#catalog-rows"), botones=page.locator("#catalog-rows button").count(),
                    formulario_alta=page.locator("#instrument-form").count()))
    shot(page, "08_catalogo_operador_solo_consulta.png")
    page.click("button[data-view=auditoria]")
    page.wait_for_selector("#audit-items article")
    log.append(dict(paso="bitacora_operador", integridad=page.inner_text("#audit-integrity"),
                    acciones=[h.inner_text() for h in page.locator("#audit-items h3").all()][:5]))
    shot(page, "09_bitacora_operador.png")
    log.append(dict(errores_consola=errors))
    browser.close()

(OUT / "recorrido.json").write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(log, ensure_ascii=False, indent=2))
