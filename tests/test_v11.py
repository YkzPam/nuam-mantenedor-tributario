"""Regresión de la versión 1.1: correcciones D3, registro operativo y permiso de factores.

Usa bases temporales; no toca data/ ni la base de la demostración visible.
"""
import importlib
import io
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))
import app as demo
from domain import CSV_COLUMNS, ValidationError, validate_rating

PAYLOAD = dict(broker=1, market="SCL", period="2026-10", instrument="V11-ONE",
               rating="Tributaria v11", registered="0", mode="monto", amount="250", base="1000")
LOG_FIELDS = {"fecha", "metodo", "ruta", "estado", "ms", "rol"}


class Version11Cases(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="nuam-v11-")
        self.root = Path(self.workspace.name)
        self.application = demo.create_app(self.root, testing=True)
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

    def post(self, client, path, payload):
        return client.post(path, json=payload, headers={"X-CSRF-Token": self.token(client)})

    def log_lines(self):
        path = Path(self.application.config["OPERATION_LOG"])
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]

    def sql(self, query, params=()):
        with sqlite3.connect(self.application.config["DATABASE"]) as conn:
            return conn.execute(query, params).fetchall()

    def test_V01_instrument_pattern_valid_and_equivalent(self):
        """V01 | regresión D3 | pattern con guion escapado y misma aceptación que el servidor"""
        html = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
        pattern = re.search(r'<input id="rating-instrument"[^>]*pattern="([^"]+)"', html).group(1)
        self.assertEqual(pattern, r"[A-Za-z0-9][A-Za-z0-9._\-]{0,39}")
        # Con la bandera v de los navegadores actuales, un guion sin escapar en la clase invalida la expresión.
        second_class = re.search(r"\]\[([^\]]+)\]", pattern).group(1)
        self.assertNotRegex(second_class.replace("\\-", ""), "-(?!Z|z|9)")
        samples = ["DEMO-ALFA", "demo.beta_1", "A", "A" * 40, "A" * 41, "-DEMO", "DEMO@1", "DEMO 1", "DEMO/1", "Ñandú"]
        compiled = re.compile(pattern)
        mismatches = []
        for value in samples:
            browser = bool(compiled.fullmatch(value))
            try:
                validate_rating(dict(PAYLOAD, instrument=value)); server = True
            except ValidationError:
                server = False
            if browser != server:
                mismatches.append(value)
        self.details = dict(pattern=pattern, samples=samples, mismatches=mismatches)
        self.assertEqual(mismatches, [])

    def test_V02_favicon_declared_without_extra_request(self):
        """V02 | regresión | ícono embebido evita la solicitud 404 a /favicon.ico"""
        client = self.client()
        page = client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b'<link rel="icon" href="data:,">', page.data)
        self.assertIn("img-src 'self' data:", page.headers["Content-Security-Policy"])

    def test_V03_operation_log_metadata_only(self):
        """V03 | registro operativo | líneas JSON con método, ruta, estado, duración y perfil"""
        client = self.client()
        created = self.post(client, "/api/ratings", PAYLOAD)
        self.assertEqual(created.status_code, 201)
        client.get(f"/api/ratings/{created.json['id']}")
        client.get("/api/ratings?q=BUSQUEDA-PRIVADA-V11")
        lines = self.log_lines()
        raw = Path(self.application.config["OPERATION_LOG"]).read_text(encoding="utf-8")
        self.assertTrue(all(set(line) == LOG_FIELDS for line in lines))
        routes = {(line["metodo"], line["ruta"], line["estado"]) for line in lines}
        self.assertIn(("POST", "/api/login", 200), routes)
        self.assertIn(("POST", "/api/ratings", 201), routes)
        self.assertIn(("GET", "/api/ratings/<int:rid>", 200), routes)
        for secret in (demo.DEMO_PASSWORD, "BUSQUEDA-PRIVADA-V11", "V11-ONE", self.token(client)):
            self.assertNotIn(secret, raw)
        self.assertTrue(all(isinstance(line["ms"], (int, float)) and line["ms"] >= 0 for line in lines))
        self.details = dict(lines=len(lines), sample=lines[-1])

    def test_V04_rejected_requests_are_logged(self):
        """V04 | registro operativo | CSRF rechazado y ruta inexistente quedan registrados"""
        client = self.client()
        self.assertEqual(client.post("/api/ratings", json=PAYLOAD).status_code, 403)
        self.assertEqual(client.get("/api/no-existe").status_code, 404)
        lines = self.log_lines()
        self.assertIn(("POST", "/api/ratings", 403), {(l["metodo"], l["ruta"], l["estado"]) for l in lines})
        self.assertIn(("GET", "sin_ruta", 404), {(l["metodo"], l["ruta"], l["estado"]) for l in lines})

    def test_V09_operation_log_rotation_keeps_three_backups(self):
        """V09 | registro operativo | rotación por tamaño con tres archivos anteriores como máximo"""
        import logging
        target = self.root / "rotacion" / "operacion.log"
        handler = demo.OperationLogHandler(target, max_bytes=200, backups=3)
        logger = logging.Logger("v11-rotacion", logging.INFO)
        logger.addHandler(handler)
        for number in range(60):
            logger.info(json.dumps(dict(linea=number, relleno="x" * 40)))
        names = sorted(path.name for path in target.parent.iterdir())
        self.assertEqual(names, ["operacion.log", "operacion.log.1", "operacion.log.2", "operacion.log.3"])
        last = json.loads(target.read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual(last["linea"], 59)
        self.details = dict(files=names)

    def test_V10_sqlite_wal_enabled(self):
        """V10 | optimización | SQLite en modo WAL con llaves foráneas activas en cada conexión"""
        with sqlite3.connect(self.application.config["DATABASE"]) as conn:
            self.assertEqual(conn.execute("PRAGMA journal_mode").fetchone()[0], "wal")
        with self.application.app_context():
            self.assertEqual(self.application.db().execute("PRAGMA foreign_keys").fetchone()[0], 1)

    def test_V05_factor_roles_from_environment(self):
        """V05 | configuración | NUAM_ROLES_FACTOR_MANUAL respeta la matriz y rechaza perfiles ajenos"""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("NUAM_ROLES_FACTOR_MANUAL", None)
            self.assertEqual(demo.factor_roles_from_env(), ("operador", "supervisor"))
        with patch.dict(os.environ, {"NUAM_ROLES_FACTOR_MANUAL": "supervisor, supervisor"}):
            self.assertEqual(demo.factor_roles_from_env(), ("supervisor",))
        with patch.dict(os.environ, {"NUAM_ROLES_FACTOR_MANUAL": "supervisor,administrador"}):
            with self.assertRaises(ValueError):
                demo.factor_roles_from_env()

    def test_V06_factor_restricted_profile_denied_and_audited(self):
        """V06 | permisos | perfil sin autorización no ingresa factores; monto sigue disponible"""
        self.application.config["ROLES_FACTOR_MANUAL"] = ("supervisor",)
        operator = self.client("operador_a")
        denied = self.post(operator, "/api/ratings", dict(PAYLOAD, instrument="V11-FACTOR", mode="factor", factor="0.25"))
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(self.sql("SELECT count(*) FROM calificacion WHERE instrumento='V11-FACTOR'")[0][0], 0)
        self.assertEqual(self.sql("SELECT count(*) FROM evento_auditoria WHERE accion='factor_manual_denegado'")[0][0], 1)
        self.assertEqual(self.post(operator, "/api/ratings", dict(PAYLOAD, instrument="V11-MONTO")).status_code, 201)
        page = operator.get("/").data.decode("utf-8")
        self.assertIn('<option value="factor" disabled>', page)
        self.assertIn('<option value="factores-DEMO" disabled>', page)
        supervisor = self.client("supervisor")
        allowed = self.post(supervisor, "/api/ratings", dict(PAYLOAD, instrument="V11-FACTOR", mode="factor", factor="0.25"))
        self.assertEqual(allowed.status_code, 201)
        self.assertIn('<option value="factor">', supervisor.get("/").data.decode("utf-8"))

    def test_V07_factor_batch_denied_for_restricted_profile(self):
        """V07 | permisos | carga factores-DEMO rechazada antes de crear lote o archivos"""
        self.application.config["ROLES_FACTOR_MANUAL"] = ("supervisor",)
        operator = self.client("operador_a")
        content = (",".join(CSV_COLUMNS) + "\nSCL,2026-10,V11-LOTE,Demo,factor,,,0.25,0\n").encode()
        response = operator.post("/api/batches/preview",
                                 data={"broker": "1", "kind": "factores-DEMO", "file": (io.BytesIO(content), "f.csv")},
                                 headers={"X-CSRF-Token": self.token(operator)})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.sql("SELECT count(*) FROM carga")[0][0], 0)
        private = [p.name for p in Path(self.application.config["PRIVATE"]).iterdir() if p.name != "reportes.tinydb.json"]
        self.assertEqual(private, [])

    def test_V08_wsgi_entrypoint_uses_data_dir(self):
        """V08 | entorno | wsgi.py expone la aplicación y respeta NUAM_DATA_DIR"""
        target = self.root / "wsgi-data"
        with patch.dict(os.environ, {"NUAM_DATA_DIR": str(target)}):
            sys.modules.pop("wsgi", None)
            module = importlib.import_module("wsgi")
        try:
            self.assertEqual(module.app.config["DATABASE"], str(target / "demo.sqlite3"))
            self.assertTrue((target / "demo.sqlite3").is_file())
            self.assertEqual(module.app.test_client().get("/api/me").status_code, 200)
        finally:
            sys.modules.pop("wsgi", None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
