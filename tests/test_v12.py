"""Regresión de la versión 1.2: reglas DEMO-2 (catálogo de instrumentos) y DEMO-3 (prioridad Bolsa).

Ambas reglas fueron definidas por el equipo para la demostración y quedan pendientes de
validación de NUAM. Cada caso usa una base temporal; no toca data/ ni la demo visible.
"""
from contextlib import closing
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))
import app as demo

HEADER = "market,period,instrument,rating,mode,amount,base,factor,registered\n"
PAYLOAD = dict(broker=1, market="SCL", period="2026-10", instrument="W12-NUEVO",
               rating="Tributaria v12", registered="0", mode="monto", amount="250", base="1000")
BOLSA_ALFA = "SCL,2026-10,DEMO-ALFA,Tributaria demo,factor,,,0.300000,1"


class Version12Cases(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="nuam-v12-")
        self.root = Path(self.workspace.name)
        self.application = demo.create_app(self.root / "datos", testing=True)
        demo.RATE_FAILURES.clear()
        self.details = {}

    def tearDown(self):
        self.workspace.cleanup()

    def token(self, client):
        return client.get("/api/me").json["csrf"]

    def client(self, login="operador_a"):
        client = self.application.test_client()
        response = client.post("/api/login", json=dict(login=login, password=demo.DEMO_PASSWORD),
                               headers={"X-CSRF-Token": self.token(client)})
        self.assertEqual(response.status_code, 200)
        return client

    def send(self, client, method, path, payload=None):
        return getattr(client, method)(path, json=payload if payload is not None else {},
                                       headers={"X-CSRF-Token": self.token(client)})

    def preview(self, client, rows, kind="DJ1948-DEMO", broker=1):
        content = (HEADER + "".join(row + "\n" for row in rows)).encode()
        return client.post("/api/batches/preview", data=dict(broker=str(broker), kind=kind,
                           file=(io.BytesIO(content), "w12.csv", "text/csv")),
                           headers={"X-CSRF-Token": self.token(client)}, content_type="multipart/form-data")

    def sql(self, query, params=()):
        # closing(): en Windows un archivo SQLite abierto impide borrar la carpeta temporal.
        with closing(sqlite3.connect(self.application.config["DATABASE"])) as conn:
            return conn.execute(query, params).fetchall()

    def alfa(self):
        return self.sql("SELECT id,origen,factor,monto,version,activo FROM calificacion "
                        "WHERE corredor_id=1 AND instrumento='DEMO-ALFA' AND activo=1")

    def test_W01_seeded_catalog_and_access(self):
        """W01 | DEMO-2 | catálogo sembrado visible para operador y supervisor, no para administrador"""
        operator = self.client()
        response = operator.get("/api/instruments")
        self.assertEqual(response.status_code, 200)
        items = {(row["mercado"], row["codigo"]): row for row in response.json["items"]}
        self.assertEqual(items[("SCL", "DEMO-ALFA")]["inscrito"], 1)
        self.assertEqual(items[("SCL", "DEMO-SUSPENDIDO")]["habilitado"], 0)
        self.assertEqual(items[("SCL", "DEMO-NO-INSCRITO")]["inscrito"], 0)
        self.assertFalse(response.json["approved"])
        self.assertIn("DEMO-2", response.json["rule"])
        self.assertEqual(self.client("supervisor").get("/api/instruments?market=SCL&q=alfa").json["total"], 1)
        self.assertEqual(self.client("admin").get("/api/instruments").status_code, 403)
        self.details = dict(seeded=len(items), disabled=[code for (market, code), row in items.items() if not row["habilitado"]])

    def test_W02_registered_instrument_must_exist(self):
        """W02 | DEMO-2 | un instrumento inscrito ausente del catálogo se rechaza sin cambios"""
        operator = self.client()
        before = self.sql("SELECT count(*) FROM evento_auditoria")[0][0]
        response = self.send(operator, "post", "/api/ratings", dict(PAYLOAD, registered="1"))
        self.assertEqual(response.status_code, 422)
        self.assertIn("DEMO-2", response.json["error"])
        self.assertEqual(self.sql("SELECT count(*) FROM calificacion WHERE instrumento='W12-NUEVO'")[0][0], 0)
        self.assertEqual(self.sql("SELECT count(*) FROM instrumento WHERE codigo='W12-NUEVO'")[0][0], 0)
        self.assertEqual(self.sql("SELECT count(*) FROM evento_auditoria")[0][0], before)
        self.details = dict(status=response.status_code, message=response.json["error"])

    def test_W03_supervisor_adds_instrument_then_it_can_be_used(self):
        """W03 | DEMO-2 | el no inscrito fuera del catálogo se admite; el supervisor agrega un inscrito y queda en la bitácora"""
        operator, supervisor = self.client(), self.client("supervisor")
        catalog_before = self.sql("SELECT count(*) FROM instrumento")[0][0]
        self.assertEqual(self.send(operator, "post", "/api/ratings", PAYLOAD).status_code, 201)
        self.assertEqual(self.sql("SELECT count(*) FROM instrumento")[0][0], catalog_before, "Un no inscrito no modifica el catálogo")
        self.assertEqual(self.send(operator, "post", "/api/ratings", dict(PAYLOAD, instrument="W12-INSCRITO", registered="1")).status_code, 422)
        added = self.send(supervisor, "post", "/api/instruments", dict(market="scl", code="w12-inscrito", registered="1"))
        self.assertEqual(added.status_code, 201)
        self.assertEqual(self.sql("SELECT mercado,codigo,inscrito,habilitado FROM instrumento WHERE id=?", (added.json["id"],)),
                         [("SCL", "W12-INSCRITO", 1, 1)])
        self.assertEqual(self.send(operator, "post", "/api/ratings", dict(PAYLOAD, instrument="W12-INSCRITO", registered="1")).status_code, 201)
        audit = supervisor.get("/api/audit").json
        self.assertIn("agregar_instrumento", [row["accion"] for row in audit["items"]])
        self.assertTrue(audit["integrity"])
        self.details = dict(added_id=added.json["id"], catalog_after=self.sql("SELECT count(*) FROM instrumento")[0][0])

    def test_W04_registration_flag_must_match_catalog(self):
        """W04 | DEMO-2 | la inscripción informada debe coincidir con la del catálogo"""
        operator = self.client()
        wrong_registered = self.send(operator, "post", "/api/ratings", dict(PAYLOAD, instrument="DEMO-ALFA", rating="Nueva", registered="0"))
        wrong_unregistered = self.send(operator, "post", "/api/ratings", dict(PAYLOAD, instrument="DEMO-NO-INSCRITO", rating="Nueva", registered="1"))
        self.assertEqual((wrong_registered.status_code, wrong_unregistered.status_code), (422, 422))
        self.assertIn("inscrito", wrong_registered.json["error"])
        self.assertIn("no inscrito", wrong_unregistered.json["error"])
        valid = self.send(operator, "post", "/api/ratings", dict(PAYLOAD, instrument="DEMO-ALFA", rating="Nueva", registered="1"))
        self.assertEqual(valid.status_code, 201)
        self.details = dict(messages=[wrong_registered.json["error"], wrong_unregistered.json["error"]])

    def test_W05_disabled_instrument_and_supervisor_toggle(self):
        """W05 | DEMO-2 | instrumento deshabilitado se rechaza; solo el supervisor cambia el catálogo"""
        operator, supervisor = self.client(), self.client("supervisor")
        suspended = self.send(operator, "post", "/api/ratings", dict(PAYLOAD, instrument="DEMO-SUSPENDIDO", registered="1"))
        self.assertEqual(suspended.status_code, 422)
        self.assertIn("deshabilitado", suspended.json["error"])
        alfa = self.sql("SELECT id,version FROM instrumento WHERE codigo='DEMO-ALFA'")[0]
        denied = self.send(operator, "put", f"/api/instruments/{alfa[0]}", dict(enabled=False, version=alfa[1]))
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(self.sql("SELECT habilitado FROM instrumento WHERE id=?", (alfa[0],)), [(1,)])
        self.assertEqual(self.send(supervisor, "put", f"/api/instruments/{alfa[0]}", dict(enabled="no", version=alfa[1])).status_code, 422)
        self.assertEqual(self.send(supervisor, "put", f"/api/instruments/{alfa[0]}", dict(enabled=False, version=alfa[1])).status_code, 200)
        self.assertEqual(self.send(supervisor, "put", f"/api/instruments/{alfa[0]}", dict(enabled=True, version=alfa[1])).status_code, 409)
        blocked = self.send(operator, "post", "/api/ratings", dict(PAYLOAD, instrument="DEMO-ALFA", rating="Nueva", registered="1"))
        self.assertEqual(blocked.status_code, 422)
        self.assertEqual(len(self.alfa()), 1, "Deshabilitar no altera la calificación ya guardada")
        self.assertIn("deshabilitar_instrumento", [row["accion"] for row in supervisor.get("/api/audit").json["items"]])
        self.assertEqual(self.send(supervisor, "put", f"/api/instruments/{alfa[0]}", dict(enabled=True, version=alfa[1] + 1)).status_code, 200)
        self.assertEqual(self.send(operator, "post", "/api/ratings", dict(PAYLOAD, instrument="DEMO-ALFA", rating="Nueva", registered="1")).status_code, 201)
        self.details = dict(suspended=suspended.json["error"], operator_toggle=denied.status_code)

    def test_W06_catalog_change_after_preview_rolls_back(self):
        """W06 | DEMO-2 | si el catálogo cambia entre previsualizar y confirmar, la carga completa se revierte"""
        operator, supervisor = self.client(), self.client("supervisor")
        rows = ["SCL,2026-10,W12-LOTE,Demo,monto,1,2,,0", "SCL,2026-10,DEMO-ALFA,Lote nuevo,monto,1,2,,1"]
        result = self.preview(operator, rows)
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.json["can_confirm"])
        alfa = self.sql("SELECT id,version FROM instrumento WHERE codigo='DEMO-ALFA'")[0]
        self.assertEqual(self.send(supervisor, "put", f"/api/instruments/{alfa[0]}", dict(enabled=False, version=alfa[1])).status_code, 200)
        confirmation = self.send(operator, "post", f"/api/batches/{result.json['id']}/confirm")
        self.assertEqual(confirmation.status_code, 409)
        self.assertIn("catálogo de instrumentos cambió", confirmation.json["error"])
        self.assertEqual(self.sql("SELECT estado FROM carga WHERE id=?", (result.json["id"],)), [("lista",)])
        self.assertEqual(self.sql("SELECT count(*) FROM calificacion WHERE instrumento='W12-LOTE'")[0][0], 0)
        self.details = dict(status=confirmation.status_code, message=confirmation.json["error"])

    def test_W07_bolsa_load_restricted_to_supervisor(self):
        """W07 | DEMO-3 | solo el supervisor previsualiza archivos de Bolsa y descarga su plantilla"""
        operator, supervisor = self.client(), self.client("supervisor")
        batches = self.sql("SELECT count(*) FROM carga")[0][0]
        denied = self.preview(operator, [BOLSA_ALFA], kind="bolsa-DEMO")
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(self.sql("SELECT count(*) FROM carga")[0][0], batches)
        self.assertEqual(self.sql("SELECT count(*) FROM evento_auditoria WHERE accion='carga_bolsa_denegada'")[0][0], 1)
        self.assertEqual(operator.get("/api/template/bolsa").status_code, 403)
        template = supervisor.get("/api/template/bolsa")
        self.assertEqual(template.status_code, 200)
        self.assertIn(b"DEMO-ALFA", template.data)
        self.details = dict(operator_preview=denied.status_code, supervisor_template=template.status_code)

    def test_W08_bolsa_replaces_broker_record_with_audit(self):
        """W08 | DEMO-3 | el archivo de Bolsa reemplaza el registro del corredor y la bitácora conserva el anterior"""
        supervisor = self.client("supervisor")
        original = self.alfa()
        self.assertEqual(original[0][1:3], ("manual", "0.250000"))
        result = self.preview(supervisor, [BOLSA_ALFA], kind="bolsa-DEMO")
        self.assertEqual(result.status_code, 200)
        self.assertEqual((result.json["invalid"], result.json["replacements"]), (0, 1))
        self.assertIn(f"registro {original[0][0]}", result.json["rows"][0]["notice"])
        confirmation = self.send(supervisor, "post", f"/api/batches/{result.json['id']}/confirm")
        self.assertEqual(confirmation.status_code, 200)
        self.assertEqual((confirmation.json["inserted"], confirmation.json["replaced"]), (1, 1))
        self.assertEqual(self.alfa(), [(original[0][0], "bolsa-DEMO", "0.300000", None, 2, 1)])
        event = self.sql("SELECT antes_json,despues_json FROM evento_auditoria WHERE accion='prioridad_bolsa' AND registro_id=?", (original[0][0],))
        self.assertEqual(len(event), 1)
        self.assertEqual((json.loads(event[0][0])["origen"], json.loads(event[0][0])["factor"]), ("manual", "0.250000"))
        self.assertEqual((json.loads(event[0][1])["origen"], json.loads(event[0][1])["factor"]), ("bolsa-DEMO", "0.300000"))
        self.assertTrue(supervisor.get("/api/audit").json["integrity"])
        filtered = self.client().get("/api/ratings?origin=bolsa-DEMO").json
        self.assertEqual(filtered["total"], 1)
        self.details = dict(before=original[0][1:3], after=self.alfa()[0][1:3], notice=result.json["rows"][0]["notice"])

    def test_W09_bolsa_over_bolsa_is_duplicate(self):
        """W09 | DEMO-3 | un segundo archivo de Bolsa con la misma llave se rechaza como duplicado"""
        supervisor = self.client("supervisor")
        first = self.preview(supervisor, [BOLSA_ALFA], kind="bolsa-DEMO")
        self.assertEqual(self.send(supervisor, "post", f"/api/batches/{first.json['id']}/confirm").status_code, 200)
        second = self.preview(supervisor, ["SCL,2026-10,DEMO-ALFA,Tributaria demo,factor,,,0.400000,1"], kind="bolsa-DEMO")
        self.assertEqual(second.json["invalid"], 1)
        self.assertFalse(second.json["can_confirm"])
        self.assertIn("ya existe un registro informado por Bolsa", second.json["rows"][0]["errors"][0])
        self.assertEqual(self.send(supervisor, "post", f"/api/batches/{second.json['id']}/confirm").status_code, 409)
        self.assertEqual(self.alfa()[0][2], "0.300000")
        self.details = dict(error=second.json["rows"][0]["errors"][0])

    def test_W10_broker_data_cannot_override_bolsa(self):
        """W10 | DEMO-3 | registro manual o carga del corredor no reemplaza un registro informado por Bolsa"""
        supervisor, operator = self.client("supervisor"), self.client()
        result = self.preview(supervisor, [BOLSA_ALFA], kind="bolsa-DEMO")
        self.assertEqual(self.send(supervisor, "post", f"/api/batches/{result.json['id']}/confirm").status_code, 200)
        manual = self.send(operator, "post", "/api/ratings", dict(PAYLOAD, instrument="DEMO-ALFA", rating="Tributaria demo", registered="1"))
        self.assertEqual(manual.status_code, 409)
        self.assertIn("DEMO-3", manual.json["error"])
        batch = self.preview(operator, ["SCL,2026-10,DEMO-ALFA,Tributaria demo,monto,1,2,,1"])
        self.assertEqual(batch.json["invalid"], 1)
        self.assertIn("DEMO-3", batch.json["rows"][0]["errors"][0])
        self.assertEqual(self.alfa()[0][1:3], ("bolsa-DEMO", "0.300000"))
        self.details = dict(manual=manual.json["error"], batch=batch.json["rows"][0]["errors"][0])

    def test_W11_operator_cannot_change_bolsa_record(self):
        """W11 | DEMO-3 | el operador no modifica ni desactiva un registro de Bolsa; el supervisor sí"""
        supervisor, operator = self.client("supervisor"), self.client()
        result = self.preview(supervisor, [BOLSA_ALFA], kind="bolsa-DEMO")
        self.assertEqual(self.send(supervisor, "post", f"/api/batches/{result.json['id']}/confirm").status_code, 200)
        rid = self.alfa()[0][0]
        change = dict(PAYLOAD, instrument="DEMO-ALFA", rating="Tributaria demo", registered="1", mode="factor", factor="0.5", version=2)
        self.assertEqual(self.send(operator, "put", f"/api/ratings/{rid}", change).status_code, 403)
        self.assertEqual(self.send(operator, "delete", f"/api/ratings/{rid}", dict(version=2)).status_code, 403)
        self.assertEqual(self.sql("SELECT count(*) FROM evento_auditoria WHERE accion='prioridad_bolsa_denegada'")[0][0], 2)
        self.assertEqual(self.alfa()[0][2:6], ("0.300000", None, 2, 1))
        self.assertEqual(self.send(supervisor, "put", f"/api/ratings/{rid}", change).status_code, 200)
        self.assertEqual(self.alfa()[0][1:3], ("bolsa-DEMO", "0.500000"))
        self.assertEqual(self.send(supervisor, "delete", f"/api/ratings/{rid}", dict(version=3)).status_code, 200)
        self.assertEqual(self.alfa(), [])
        self.details = dict(operator_put=403, operator_delete=403, supervisor="modifica y desactiva")

    def test_W12_bolsa_new_key_and_factor_mode(self):
        """W12 | DEMO-3 | una llave nueva de Bolsa se inserta con origen bolsa-DEMO y exige mode=factor"""
        supervisor = self.client("supervisor")
        rows = ["SCL,2026-10,DEMO-BETA,Tributaria demo,factor,,,0.200000,1", "SCL,2026-10,W12-BOLSA,Demo,monto,1,2,,0"]
        mixed = self.preview(supervisor, rows, kind="bolsa-DEMO")
        self.assertEqual(mixed.json["invalid"], 1)
        self.assertIn("requiere mode=factor", mixed.json["rows"][1]["errors"][0])
        result = self.preview(supervisor, rows[:1], kind="bolsa-DEMO")
        self.assertEqual(result.json["replacements"], 0)
        confirmation = self.send(supervisor, "post", f"/api/batches/{result.json['id']}/confirm")
        self.assertEqual((confirmation.json["inserted"], confirmation.json["replaced"]), (1, 0))
        self.assertEqual(self.sql("SELECT origen,factor FROM calificacion WHERE corredor_id=1 AND instrumento='DEMO-BETA' AND activo=1"),
                         [("bolsa-DEMO", "0.200000")])
        self.details = dict(mode_error=mixed.json["rows"][1]["errors"][0])

    def test_W13_bolsa_prevails_over_record_created_after_preview(self):
        """W13 | DEMO-3 | si el corredor crea la misma llave después de la previsualización, Bolsa igual prevalece"""
        supervisor, operator = self.client("supervisor"), self.client()
        result = self.preview(supervisor, ["SCL,2026-10,DEMO-BETA,Tributaria demo,factor,,,0.200000,1"], kind="bolsa-DEMO")
        self.assertEqual(result.json["replacements"], 0)
        created = self.send(operator, "post", "/api/ratings", dict(PAYLOAD, instrument="DEMO-BETA", rating="Tributaria demo", registered="1"))
        self.assertEqual(created.status_code, 201)
        confirmation = self.send(supervisor, "post", f"/api/batches/{result.json['id']}/confirm")
        self.assertEqual(confirmation.status_code, 200)
        self.assertEqual(confirmation.json["replaced"], 1)
        self.assertEqual(self.sql("SELECT id,origen,factor FROM calificacion WHERE corredor_id=1 AND instrumento='DEMO-BETA' AND activo=1"),
                         [(created.json["id"], "bolsa-DEMO", "0.200000")])
        self.details = dict(replaced_id=created.json["id"])

    def test_W14_previous_schema_is_backed_up(self):
        """W14 | migración | una base anterior a la v1.2 se respalda completa y se crea un esquema nuevo"""
        old = self.root / "anterior"
        (old / "private").mkdir(parents=True)
        (old / "private" / "reporte.json").write_text("{}", encoding="utf-8")
        with closing(sqlite3.connect(old / "demo.sqlite3")) as conn:
            conn.execute("CREATE TABLE calificacion (id INTEGER PRIMARY KEY)")
            conn.commit()
        upgraded = demo.create_app(old, testing=True)
        backups = sorted(old.glob("respaldo_v1_*"))
        self.assertEqual(len(backups), 1)
        self.assertTrue((backups[0] / "demo.sqlite3").is_file())
        self.assertTrue((backups[0] / "private" / "reporte.json").is_file())
        self.assertEqual(upgraded.config["SCHEMA_BACKUP"], str(backups[0]))
        with closing(sqlite3.connect(old / "demo.sqlite3")) as conn:
            self.assertEqual(conn.execute("PRAGMA user_version").fetchone()[0], 2)
            self.assertEqual(conn.execute("SELECT count(*) FROM instrumento").fetchone()[0], len(demo.CATALOG_SEED))
        again = demo.create_app(old, testing=True)
        self.assertIsNone(again.config["SCHEMA_BACKUP"])
        self.assertEqual(len(sorted(old.glob("respaldo_v1_*"))), 1)
        self.details = dict(backup=backups[0].name)

    def test_W15_supplied_examples_06_07(self):
        """W15 | ejemplos | 06 reemplaza por prioridad Bolsa y 07 se rechaza completo por catálogo"""
        supervisor = self.client("supervisor")
        replace = self.preview(supervisor, (ROOT / "ejemplos" / "06_bolsa_prioridad.csv").read_text(encoding="utf-8").splitlines()[1:], kind="bolsa-DEMO")
        self.assertEqual((replace.json["invalid"], replace.json["replacements"]), (0, 1))
        rejected = self.preview(supervisor, (ROOT / "ejemplos" / "07_catalogo_rechazos.csv").read_text(encoding="utf-8").splitlines()[1:])
        self.assertEqual(rejected.json["invalid"], 2)
        errors = [row["errors"][0] for row in rejected.json["rows"]]
        self.assertIn("deshabilitado", errors[0])
        self.assertIn("debe existir en el catálogo", errors[1])
        self.assertEqual(self.send(supervisor, "post", f"/api/batches/{rejected.json['id']}/confirm").status_code, 409)
        self.details = dict(example_06=replace.json["replacements"], example_07=errors)

    def test_W16_interface_exposes_rules_by_profile(self):
        """W16 | interfaz | catálogo para ambos perfiles; opción y plantilla de Bolsa solo para supervisor"""
        operator_html = self.client().get("/").get_data(as_text=True)
        supervisor_html = self.client("supervisor").get("/").get_data(as_text=True)
        for html in (operator_html, supervisor_html):
            self.assertIn('data-view="catalogo"', html)
            self.assertIn('<option>bolsa-DEMO</option>', html)
            self.assertIn('list="instrument-options"', html)
            self.assertNotIn("inactivar", html.lower())
        self.assertNotIn('value="bolsa-DEMO"', operator_html)
        self.assertNotIn("/api/template/bolsa", operator_html)
        self.assertNotIn('id="instrument-form"', operator_html)
        self.assertIn('value="bolsa-DEMO"', supervisor_html)
        self.assertIn("/api/template/bolsa", supervisor_html)
        self.assertIn('id="instrument-form"', supervisor_html)
        javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        self.assertIn("Regla DEMO-3: solo el supervisor cambia registros informados por Bolsa.", javascript)
        self.assertNotIn("innerHTML", javascript)
        self.details = dict(operator_bolsa_option=False, supervisor_bolsa_option=True)

    def test_W17_catalog_changes_apply_forward(self):
        """W17 | DEMO-2 | un cambio del catálogo rige hacia adelante: no altera registros guardados y revierte confirmaciones pendientes"""
        supervisor, operator = self.client("supervisor"), self.client()
        pending = self.preview(supervisor, [BOLSA_ALFA], kind="bolsa-DEMO")
        self.assertEqual(pending.json["replacements"], 1)
        rid, alfa = self.alfa()[0][0], self.sql("SELECT id,version FROM instrumento WHERE codigo='DEMO-ALFA'")[0]
        self.assertEqual(self.send(supervisor, "put", f"/api/instruments/{alfa[0]}", dict(enabled=False, version=alfa[1])).status_code, 200)
        self.assertEqual(self.alfa(), [(rid, "manual", "0.250000", "250", 1, 1)])
        change = dict(PAYLOAD, instrument="DEMO-ALFA", rating="Tributaria demo", registered="1", amount="300", version=1)
        modified = self.send(operator, "put", f"/api/ratings/{rid}", change)
        self.assertEqual(modified.status_code, 422)
        self.assertIn("deshabilitado", modified.json["error"])
        confirmation = self.send(supervisor, "post", f"/api/batches/{pending.json['id']}/confirm")
        self.assertEqual(confirmation.status_code, 409)
        self.assertIn("catálogo de instrumentos cambió", confirmation.json["error"])
        self.assertEqual(self.alfa()[0][1:3], ("manual", "0.250000"))
        self.assertEqual(self.send(operator, "delete", f"/api/ratings/{rid}", dict(version=1)).status_code, 200)
        self.assertEqual(self.alfa(), [])
        self.details = dict(update=modified.status_code, bolsa_confirm=confirmation.status_code, deactivate=200)

    def test_W18_add_instrument_validation(self):
        """W18 | DEMO-2 | alta de instrumentos: solo supervisor, datos válidos y sin duplicados"""
        operator, supervisor = self.client(), self.client("supervisor")
        self.assertEqual(self.send(operator, "post", "/api/instruments", dict(market="SCL", code="W12-X", registered="1")).status_code, 403)
        for payload in [dict(market="OTRO", code="W12-X", registered="1"), dict(market="SCL", code="<script>", registered="1"),
                        dict(market="SCL", code="W12-X", registered="2")]:
            self.assertEqual(self.send(supervisor, "post", "/api/instruments", payload).status_code, 422)
        duplicate = self.send(supervisor, "post", "/api/instruments", dict(market="SCL", code="DEMO-ALFA", registered="1"))
        self.assertEqual(duplicate.status_code, 409)
        self.assertNotIn("UNIQUE", duplicate.json["error"])
        self.assertEqual(self.sql("SELECT count(*) FROM instrumento WHERE codigo='W12-X'")[0][0], 0)
        self.details = dict(duplicate=duplicate.json["error"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
