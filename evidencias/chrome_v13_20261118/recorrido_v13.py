import sys, re
from pathlib import Path
from playwright.sync_api import sync_playwright
EX=Path(sys.argv[1])/"ejemplos"; OUT=Path(sys.argv[2]); OUT.mkdir(exist_ok=True); B="http://127.0.0.1:8765"; err=[]; bad=[]
BAN=re.compile(r"ficti|demostraci|ilustrativ|demo|académic",re.I)
def scan(p,name):
    t=p.locator("body").inner_text()
    for m in BAN.finditer(t): bad.append((name,t[max(0,m.start()-40):m.end()+40]))
def login(p,u):
    p.goto(B+"/"); p.fill("#login",u); p.fill("#password","Clave2026!"); p.click("#login-form button[type=submit]"); p.wait_for_selector("#logout"); p.wait_for_timeout(900)
with sync_playwright() as pw:
    b=pw.chromium.launch(); p=b.new_page(viewport={"width":1366,"height":800})
    p.on("pageerror",lambda e: err.append(str(e))); p.on("console",lambda m: err.append(m.text) if m.type=="error" else None)
    p.goto(B+"/"); p.wait_for_timeout(600); scan(p,"login"); p.screenshot(path=str(OUT/"01_login.jpg"))
    login(p,"operador_a"); p.fill("#filter-query","INS-ALFA"); p.click("#search-form button[type=submit]"); p.wait_for_timeout(800)
    print("T1:", " ".join(p.locator("#rating-rows tr").first.inner_text().split())); scan(p,"consulta"); p.screenshot(path=str(OUT/"02_consulta.jpg"))
    p.click("#clear-filter"); p.wait_for_timeout(400); p.click("#new-rating"); p.wait_for_selector("#edit-dialog[open]")
    p.select_option("#rating-market","SCL"); p.fill("#rating-period","2026-10"); p.fill("#rating-instrument","INS-BETA"); p.fill("#rating-name","Tributaria general")
    p.select_option("#rating-registered","1"); p.select_option("#rating-mode","monto"); p.fill("#rating-amount","300"); p.fill("#rating-base","1000")
    scan(p,"formulario"); p.screenshot(path=str(OUT/"03_formulario.jpg")); p.click("#rating-form button[type=submit]"); p.wait_for_selector("#edit-dialog",state="hidden"); p.wait_for_timeout(700)
    print("T2:", p.locator("#message").inner_text())
    row=p.locator("#rating-rows tr",has_text="INS-BETA").first; row.get_by_role("button",name="Detalle").click(); p.wait_for_selector("#detail-dialog[open]"); scan(p,"detalle"); p.screenshot(path=str(OUT/"04_detalle.jpg")); p.locator("#detail-dialog .close-detail").first.click()
    row.get_by_role("button",name="Modificar").click(); p.wait_for_selector("#edit-dialog[open]"); p.fill("#rating-amount","350"); p.click("#rating-form button[type=submit]"); p.wait_for_selector("#edit-dialog",state="hidden"); p.wait_for_timeout(600)
    print("T3:", " ".join(p.locator("#rating-rows tr",has_text="INS-BETA").first.inner_text().split()))
    p.click("button[data-view=carga]"); p.set_input_files("#batch-file",str(EX/"03_campos_incompletos.csv")); p.click("#upload-form button[type=submit]"); p.wait_for_selector("#preview:not([hidden])"); p.wait_for_timeout(700)
    print("T4:", " ".join(p.locator("#preview").inner_text().split())[:220]); scan(p,"carga"); p.screenshot(path=str(OUT/"05_carga.jpg"),full_page=True)
    p.set_input_files("#batch-file",str(EX/"01_montos_valido.csv")); p.click("#upload-form button[type=submit]"); p.wait_for_timeout(1300); p.click("#confirm-batch"); p.locator("#preview-count",has_text="confirmada").wait_for()
    print("T5:", p.locator("#preview-count").inner_text())
    p.locator("#batch-history button", has_text="Reporte").first.click() if p.locator("#batch-history button", has_text="Reporte").count() else None
    p.wait_for_timeout(800); scan(p,"historial"); 
    if p.locator("#document-dialog[open]").count(): p.screenshot(path=str(OUT/"06_reporte.jpg")); p.locator("#document-dialog .close-document").first.click()
    p.click("button[data-view=catalogo]"); p.wait_for_timeout(800); scan(p,"catalogo"); p.screenshot(path=str(OUT/"07_catalogo.jpg"))
    p.click("button[data-view=factores]"); p.click("#factor-form button[type=submit]"); p.wait_for_timeout(700); print("factor:", p.locator("#factor-result").inner_text()); scan(p,"factores"); p.screenshot(path=str(OUT/"08_factores.jpg"))
    p.click("button[data-view=auditoria]"); p.wait_for_timeout(900); scan(p,"bitacora_op"); p.click("#logout"); p.wait_for_timeout(500)
    login(p,"operador_b"); p.fill("#filter-query","INS-ALFA"); p.click("#search-form button[type=submit]"); p.wait_for_timeout(800); print("op_b ve INS-ALFA:", p.locator("#rating-rows tr",has_text="INS-ALFA").count()); p.click("#logout"); p.wait_for_timeout(500)
    login(p,"supervisor"); p.click("button[data-view=carga]"); p.wait_for_timeout(500)
    print("tipos:", p.locator("#batch-kind option").all_inner_texts(), p.locator("#batch-broker option").all_inner_texts())
    p.select_option("#batch-broker", label=[o for o in p.locator("#batch-broker option").all_inner_texts() if "CORR-A" in o][0]); p.select_option("#batch-kind","bolsa")
    p.set_input_files("#batch-file",str(EX/"06_bolsa_prioridad.csv")); p.click("#upload-form button[type=submit]"); p.wait_for_timeout(1300); print("bolsa prev:", " ".join(p.locator("#preview").inner_text().split())[:260]); scan(p,"carga_sup")
    p.click("#confirm-batch"); p.wait_for_timeout(1200); print("bolsa conf:", p.locator("#preview-count").inner_text())
    p.select_option("#batch-kind","montos"); p.set_input_files("#batch-file",str(EX/"07_catalogo_rechazos.csv")); p.click("#upload-form button[type=submit]"); p.wait_for_timeout(1300); print("07:", " ".join(p.locator("#preview-rows").inner_text().split())[:260])
    p.click("button[data-view=auditoria]"); p.wait_for_timeout(1000); print("aud:", p.locator("#audit-integrity").inner_text()); scan(p,"bitacora_sup"); p.screenshot(path=str(OUT/"09_bitacora.jpg")); p.click("#logout"); p.wait_for_timeout(500)
    login(p,"operador_a"); p.fill("#filter-query","INS-ALFA"); p.click("#search-form button[type=submit]"); p.wait_for_timeout(800)
    r=p.locator("#rating-rows tr",has_text="INS-ALFA").first; print("final:", " ".join(r.inner_text().split()), "| modificar:", r.get_by_role("button",name="Modificar").is_enabled()); p.screenshot(path=str(OUT/"10_prioridad.jpg")); p.click("#logout"); p.wait_for_timeout(500)
    login(p,"admin"); p.wait_for_timeout(800); scan(p,"admin"); p.click("button[data-view=usuarios]"); p.wait_for_timeout(800); scan(p,"usuarios"); p.screenshot(path=str(OUT/"11_admin.jpg"))
    m=b.new_page(viewport={"width":390,"height":844}); m.goto(B+"/"); m.fill("#login","operador_a"); m.fill("#password","Clave2026!"); m.click("#login-form button[type=submit]"); m.wait_for_selector("#logout"); m.wait_for_timeout(900); m.screenshot(path=str(OUT/"12_movil.jpg"),full_page=False)
    b.close()
print("PROHIBIDAS:", bad); print("ERRORES:", err)
