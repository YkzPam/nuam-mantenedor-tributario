"""Regresión acotada de desactivación; no utiliza la base de la demo visible.

Los controles HTML/JavaScript se revisan estructuralmente, no como sustituto
de una comprobación de foco y presentación en un navegador real.
"""
import json
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor"))
import app as demo


class IdParser(HTMLParser):
    """Conserva atributos y texto de los elementos identificados del HTML."""
    def __init__(self, html):
        super().__init__()
        self.nodes = {}
        self.stack = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        node = {"tag": tag, "attrs": attributes, "text": ""}
        if "id" in attributes:
            self.nodes[attributes["id"]] = node
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img",
                       "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        for node in self.stack:
            node["text"] += data


class UiRevisionCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix="nuam-ui-revision-")
        cls.root = Path(cls.workspace.name)
        cls.application = demo.create_app(cls.root / "seed", testing=True)

    @classmethod
    def tearDownClass(cls):
        cls.workspace.cleanup()

    def setUp(self):
        self.case_dir = Path(tempfile.mkdtemp(prefix="case-", dir=self.root))
        (self.case_dir / "private").mkdir()
        shutil.copy2(self.root / "seed" / "demo.sqlite3", self.case_dir / "case.sqlite3")
        self.application.config["DATABASE"] = str(self.case_dir / "case.sqlite3")
        self.application.config["PRIVATE"] = str(self.case_dir / "private")
        demo.RATE_FAILURES.clear()
        self.client = self.application.test_client()
        self.login(self.client, "operador_a")
        self.html = self.client.get("/").get_data(as_text=True)
        self.nodes = IdParser(self.html).nodes
        self.javascript = (ROOT / "static" / "app.js").read_text(encoding="utf-8")
        self.stylesheet = (ROOT / "static" / "style.css").read_text(encoding="utf-8")

    def token(self, client):
        return client.get("/api/me").json["csrf"]

    def login(self, client, username):
        response = client.post("/api/login", json={"login": username,
                               "password": demo.DEMO_PASSWORD},
                               headers={"X-CSRF-Token": self.token(client)})
        self.assertEqual(response.status_code, 200)

    def mutation(self, client, path, method="post", payload=None):
        return getattr(client, method)(path, json=payload or {},
                                       headers={"X-CSRF-Token": self.token(client)})

    def create_rating(self):
        payload = dict(broker=1, market="SCL", period="2026-10",
                       instrument="UI-REVISION", rating="Tributaria revisión",
                       registered="0", mode="monto", amount="250", base="1000")
        response = self.mutation(self.client, "/api/ratings", payload=payload)
        self.assertEqual(response.status_code, 201)
        return response.json["id"]

    def sql(self, statement, params=()):
        connection = sqlite3.connect(self.application.config["DATABASE"])
        try:
            return connection.execute(statement, params).fetchall()
        finally:
            connection.close()

    def test_UI01_consistent_visible_action_and_explanation(self):
        """UI01: acción Desactivar y explicación explícita de baja lógica."""
        self.assertIn("modificar y desactivar", self.html)
        self.assertNotIn("inactivar", self.html.lower())
        self.assertIn("action('Desactivar',()=>openDelete(row))", self.javascript)
        self.assertNotIn("action('Inactivar'", self.javascript)
        explanation = self.nodes["delete-explanation"]["text"]
        for text in ["baja lógica", "no un borrado permanente", "historial se conservan",
                     "valores anteriores y nuevos", "consulta de activos"]:
            self.assertIn(text, explanation)
        self.assertIn("Calificación desactivada. Sus datos y su historial se conservan.",
                      self.javascript)

    def test_UI02_dialog_accessible_name_description_and_safe_default(self):
        """UI02: nombre y descripción enlazados; Cancelar primero y autofocus."""
        dialog = self.nodes["delete-dialog"]
        self.assertEqual(dialog["tag"], "dialog")
        self.assertEqual(dialog["attrs"]["aria-labelledby"], "delete-title")
        self.assertEqual(dialog["attrs"]["aria-describedby"],
                         "delete-description delete-explanation")
        self.assertEqual(self.nodes["delete-title"]["text"], "Desactivar calificación")
        self.assertIn("autofocus", self.nodes["cancel-delete"]["attrs"])
        self.assertEqual(self.nodes["cancel-delete"]["attrs"]["type"], "button")
        self.assertLess(self.html.index('id="cancel-delete"'),
                        self.html.index('id="accept-delete"'))
        self.assertEqual(self.nodes["accept-delete"]["text"], "Sí, desactivar")
        self.assertEqual(self.nodes["accept-delete"]["attrs"]["type"], "button")

    def test_UI03_confirmation_identifies_record_and_preserves_safe_text_rendering(self):
        """UI03: cuatro identificadores con textContent y foco seguro explícito."""
        function = self.javascript.split("function openDelete(row){", 1)[1].split(
            "async function saveRating", 1)[0]
        self.assertIn("deleteRecord=row", function)
        self.assertIn("$('delete-description').textContent=", function)
        for key in ["row.calificacion", "row.instrumento", "row.periodo", "row.corredor"]:
            self.assertIn(key, function)
        self.assertNotIn("innerHTML", function)
        self.assertLess(function.index("$('delete-dialog').showModal()"),
                        function.index("$('cancel-delete').focus()"))
        self.assertIn("api('ratings/'+deleteRecord.id,'DELETE',{version:deleteRecord.version})",
                      self.javascript)

    def test_UI04_soft_delete_retains_data_and_audit(self):
        """UI04: desactivar oculta activos, conserva fila/datos y antes/después."""
        rid = self.create_rating()
        before = self.client.get(f"/api/ratings/{rid}").json["item"]
        response = self.mutation(self.client, f"/api/ratings/{rid}", "delete", {"version": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/ratings?q=UI-REVISION").json["total"], 0)
        after = self.client.get(f"/api/ratings/{rid}").json["item"]
        self.assertEqual(after["activo"], 0)
        self.assertEqual(after["version"], 2)
        for key in ["id", "corredor_id", "mercado", "periodo", "instrumento",
                    "calificacion", "monto", "base", "factor", "creado"]:
            self.assertEqual(after[key], before[key])
        self.assertEqual(self.sql("SELECT count(*) FROM calificacion WHERE id=?", (rid,))[0][0], 1)
        events = self.sql("SELECT antes_json,despues_json FROM evento_auditoria "
                          "WHERE accion='inactivar' AND entidad='calificacion' AND registro_id=?", (rid,))
        self.assertEqual(len(events), 1)
        self.assertEqual(json.loads(events[0][0])["activo"], 1)
        self.assertEqual(json.loads(events[0][1])["activo"], 0)
        self.assertTrue(self.client.get("/api/audit").json["integrity"])

    def test_UI05_other_corridor_cannot_deactivate(self):
        """UI05: el cambio de rótulo no altera autorización por corredor."""
        rid = self.create_rating()
        other = self.application.test_client()
        self.login(other, "operador_b")
        response = self.mutation(other, f"/api/ratings/{rid}", "delete", {"version": 1})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.sql("SELECT activo,version FROM calificacion WHERE id=?", (rid,)), [(1, 1)])
        self.assertEqual(self.sql("SELECT count(*) FROM evento_auditoria "
                                 "WHERE accion='inactivar' AND registro_id=?", (rid,))[0][0], 0)

    def test_UI06_obsolete_version_does_not_deactivate(self):
        """UI06: una confirmación obsoleta conserva el registro activo."""
        rid = self.create_rating()
        response = self.mutation(self.client, f"/api/ratings/{rid}", "delete", {"version": 0})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(self.sql("SELECT activo,version FROM calificacion WHERE id=?", (rid,)), [(1, 1)])

    def test_UI07_cancel_and_confirmation_have_distinct_scoped_styles(self):
        """UI07: Cancelar verde sólido; confirmación blanca/roja y bordes de 2 px."""
        rules = {
            selector.strip(): dict(
                declaration.strip().split(":", 1)
                for declaration in declarations.split(";") if declaration.strip()
            )
            for selector, declarations in re.findall(r"([^{}]+)\{([^{}]*)\}", self.stylesheet)
        }
        cancel = rules["#delete-dialog #cancel-delete"]
        confirmation = rules["#delete-dialog #accept-delete"]
        self.assertEqual(cancel["background"], "var(--green)")
        self.assertEqual(cancel["color"], "#fff")
        self.assertEqual(cancel["border"], "2px solid var(--green)")
        self.assertEqual(confirmation["background"], "#fff")
        self.assertEqual(confirmation["color"], "var(--danger)")
        self.assertEqual(confirmation["border"], "2px solid var(--danger)")
        self.assertNotEqual(cancel["background"], confirmation["background"])
        self.assertNotEqual(cancel["color"], confirmation["color"])
        for selector in rules:
            if "#cancel-delete" in selector or "#accept-delete" in selector:
                self.assertTrue(selector.startswith("#delete-dialog "), selector)
        self.assertEqual(rules["#delete-dialog #cancel-delete:hover"]["background"], "#104c34")
        self.assertEqual(rules["#delete-dialog #accept-delete:hover"]["background"], "#ffefef")
        self.assertIn("button:focus-visible", self.stylesheet)
        self.assertIn("outline:3px solid #ad7504;outline-offset:3px", self.stylesheet)

    def test_UI08_confirmed_batch_replaces_pending_state_only_after_success(self):
        """UI08: estado confirmado tras API exitosa; conserva una previsualización nueva."""
        handler = self.javascript.split(
            "$('confirm-batch').addEventListener('click',run(async()=>{", 1)[1].split(
            "$('factor-form').addEventListener", 1)[0]
        self.assertIn("const batchId=lastBatch", handler)
        self.assertIn("await api('batches/'+batchId+'/confirm','POST',{})", handler)
        self.assertIn("if(lastBatch===batchId)", handler)
        self.assertIn("$('preview-count').textContent='Carga '+batchId+' confirmada: '", handler)
        self.assertIn("data.inserted+' registro(s) incorporado(s). No hay una nueva confirmación pendiente.'", handler)
        self.assertNotIn("Lista para confirmación explícita", handler)
        self.assertNotIn("innerHTML", handler)
        request = handler.index("const data=await api(")
        guard = handler.index("if(lastBatch===batchId)")
        update = handler.index("$('preview-count').textContent=")
        disable = handler.index("$('confirm-batch').disabled=true")
        self.assertLess(handler.index("const batchId=lastBatch"), request)
        self.assertLess(request, guard)
        self.assertLess(guard, update)
        self.assertLess(update, disable)
        self.assertLess(disable, handler.index("await loadBatches()"))
        guarded = handler.split("if(lastBatch===batchId){", 1)[1].split("}", 1)[0]
        self.assertIn("$('preview-count').textContent=", guarded)
        self.assertIn("$('confirm-batch').disabled=true", guarded)
        api_function = self.javascript.split("async function api(", 1)[1].split(
            "function action(", 1)[0]
        self.assertLess(api_function.index("if(!response.ok) throw Error("),
                        api_function.index("return data"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
