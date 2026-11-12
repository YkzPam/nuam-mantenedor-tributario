"""Pruebas complementarias aisladas del ZIP recibido; nunca modifica su fuente."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing, contextmanager
from datetime import datetime, timezone
import gc
import hashlib
import inspect
import io
import json
import math
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import stat
import sys
import tempfile
from threading import Barrier
import time
import traceback
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor"))
sys.path.insert(0, str(ROOT))
PROTOTYPE = ROOT
import app as demo
import documentrepo

PAYLOAD = dict(broker=1, market="SCL", period="2026-10", instrument="COMP-ONE",
               rating="Tributaria complementaria", registered="0", mode="monto", amount="250", base="1000")


@contextmanager
def replace_closure(function, name, replacement):
    function = inspect.unwrap(function)
    cells = dict(zip(function.__code__.co_freevars, function.__closure__ or ()))
    cell = cells[name]
    original = cell.cell_contents
    cell.cell_contents = replacement(original)
    try:
        yield
    finally:
        cell.cell_contents = original


class ComplementaryCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="nuam-complementary-")
        cls.root = Path(cls.temporary.name)
        cls.application = demo.create_app(cls.root / "seed", testing=True)
        cls.application.config["PROPAGATE_EXCEPTIONS"] = False
        cls.application.logger.disabled = True

    @classmethod
    def tearDownClass(cls):
        gc.collect()
        cls.temporary.cleanup()

    def setUp(self):
        self.details = {}
        self.case_root = Path(tempfile.mkdtemp(prefix="case-", dir=self.root))
        (self.case_root / "private").mkdir()
        shutil.copy2(self.root / "seed" / "demo.sqlite3", self.case_root / "case.sqlite3")
        self.application.config["DATABASE"] = str(self.case_root / "case.sqlite3")
        self.application.config["PRIVATE"] = str(self.case_root / "private")
        demo.RATE_FAILURES.clear()
        self.client = self.login()

    def token(self, client):
        return client.get("/api/me").json["csrf"]

    def login(self, username="operador_a"):
        client = self.application.test_client()
        response = client.post("/api/login", json=dict(login=username, password=demo.DEMO_PASSWORD),
                               headers={"X-CSRF-Token": self.token(client)})
        self.assertEqual(response.status_code, 200)
        return client

    def request(self, method, path, payload=None, client=None, token=None):
        client = client or self.client
        return client.open(path, method=method, json=payload or {},
                           headers={"X-CSRF-Token": token if token is not None else self.token(client)})

    def query(self, statement, values=()):
        with closing(sqlite3.connect(self.application.config["DATABASE"])) as connection:
            return connection.execute(statement, values).fetchall()

    def snapshot(self):
        return {table: self.query(f"SELECT * FROM {table} ORDER BY rowid")
                for table in ["calificacion", "carga", "carga_fila", "archivo", "usuario", "usuario_corredor"]}

    def business_events(self):
        return self.query("SELECT * FROM evento_auditoria WHERE entidad IN ('calificacion','carga','usuario') ORDER BY id")

    def create(self, instrument="COMP-ONE"):
        response = self.request("POST", "/api/ratings", dict(PAYLOAD, instrument=instrument))
        self.assertEqual(response.status_code, 201)
        return response.json["id"]

    def csv(self, instruments=("COMP-BULK-1", "COMP-BULK-2")):
        return ("market,period,instrument,rating,mode,amount,base,factor,registered\n" +
                "".join(f"SCL,2026-10,{instrument},Complementaria,monto,250,1000,,0\n"
                        for instrument in instruments)).encode()

    def preview(self, content=None, client=None, csrf=None, filename="complementaria.csv", kind="DJ1948-DEMO"):
        client = client or self.client
        return client.post("/api/batches/preview", data={"broker": "1", "kind": kind,
                           "file": (io.BytesIO(content or self.csv()), filename)},
                           headers={"X-CSRF-Token": csrf if csrf is not None else self.token(client)})

    def test_CP01_twenty_concurrent_saves(self):
        """PLAN-R01: veinte guardados concurrentes, P95 y persistencia/auditoría."""
        clients = [self.login() for _ in range(20)]
        tokens = [self.token(client) for client in clients]
        gate = Barrier(20)
        def save(index):
            gate.wait()
            started = time.perf_counter()
            response = clients[index].post("/api/ratings", json=dict(PAYLOAD, instrument=f"COMP-CONCURRENT-{index}"),
                                          headers={"X-CSRF-Token": tokens[index]})
            return dict(index=index, seconds=round(time.perf_counter()-started, 6), status=response.status_code)
        with ThreadPoolExecutor(max_workers=20) as pool:
            measurements = list(pool.map(save, range(20)))
        p95 = sorted(item["seconds"] for item in measurements)[math.ceil(20*.95)-1]
        count = self.query("SELECT count(*) FROM calificacion WHERE instrumento LIKE 'COMP-CONCURRENT-%'")[0][0]
        events = self.query("SELECT count(*) FROM evento_auditoria e JOIN calificacion c ON c.id=e.registro_id "
                            "WHERE e.entidad='calificacion' AND e.accion='crear' AND c.instrumento LIKE 'COMP-CONCURRENT-%'")[0][0]
        self.details = dict(clients=20, requests=20, p95_seconds=p95, max_seconds=max(item["seconds"] for item in measurements),
                            status_codes=[item["status"] for item in measurements], persisted_rows=count,
                            business_events=events, measurements=measurements,
                            scope="Flask test_client + SQLite local, sin navegador, autenticación medida ni red NUAM")
        self.assertTrue(all(item["status"] == 201 for item in measurements))
        self.assertLessEqual(p95, 3)
        self.assertEqual((count, events), (20, 20))

    def test_CP02_preview_file_failure_cleans_every_created_file(self):
        """PLAN-I02: falla después del segundo archivo, sin SQL/documento/archivos huérfanos."""
        before, audit_before = self.snapshot(), self.business_events()
        calls = 0
        def failing(original):
            def wrapper(*args, **kwargs):
                nonlocal calls
                calls += 1
                path = original(*args, **kwargs)
                if calls == 2:
                    raise OSError("Fallo I/O inyectado después de crear el segundo archivo")
                return path
            return wrapper
        with replace_closure(self.application.view_functions["preview"], "file_record", failing):
            response = self.preview()
        orphan_files = [path.name for path in (self.case_root / "private").iterdir()
                        if path.name != "reportes.tinydb.json"]
        documents = documentrepo.reports_for_brokers(self.application.config["PRIVATE"], [1])
        self.details = dict(http_status=response.status_code, response_is_json=response.is_json,
                            sql_unchanged=self.snapshot() == before, business_audit_unchanged=self.business_events() == audit_before,
                            remaining_private_files=orphan_files, document_count=len(documents))
        self.assertIn(response.status_code, (500, 503))
        self.assertTrue(response.is_json)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.business_events(), audit_before)
        self.assertEqual(documents, [])
        self.assertEqual(orphan_files, [], "Quedó un archivo privado huérfano después del rollback de preview")

    def test_CP03_preview_document_failure_rolls_back_all_stores(self):
        """PLAN-I02: falla TinyDB tras escribir; revierte SQL, archivos y documento derivado."""
        before, audit_before = self.snapshot(), self.business_events()
        original = documentrepo.upsert_report
        def write_then_fail(*args, **kwargs):
            original(*args, **kwargs)
            raise documentrepo.DocumentStoreError("Fallo documental inyectado")
        with patch.object(documentrepo, "upsert_report", side_effect=write_then_fail):
            response = self.preview()
        files = [path.name for path in (self.case_root / "private").iterdir() if path.name != "reportes.tinydb.json"]
        documents = documentrepo.reports_for_brokers(self.application.config["PRIVATE"], [1])
        self.details = dict(http_status=response.status_code, sql_unchanged=self.snapshot() == before,
                            files_remaining=len(files), document_count=len(documents))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.business_events(), audit_before)
        self.assertEqual((files, documents), ([], []))
        retry = self.preview()
        self.assertEqual(retry.status_code, 200)
        self.details["retry_status"] = retry.status_code

    def test_CP04_confirmation_failure_after_first_insert_is_atomic(self):
        """PLAN-I02: falla en segunda fila al confirmar, sin calificación/evento parcial; reintento."""
        bid = self.preview().json["id"]
        before, audit_before = self.snapshot(), self.business_events()
        calls = 0
        def failing(original):
            def wrapper(*args, **kwargs):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise documentrepo.DocumentStoreError("Fallo intermedio de confirmación inyectado")
                return original(*args, **kwargs)
            return wrapper
        with replace_closure(self.application.view_functions["confirm_batch"], "insert_rating", failing):
            response = self.request("POST", f"/api/batches/{bid}/confirm")
        self.details = dict(http_status=response.status_code, sql_unchanged=self.snapshot() == before,
                            audit_unchanged=self.business_events() == audit_before)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(self.business_events(), audit_before)
        retry = self.request("POST", f"/api/batches/{bid}/confirm")
        self.assertEqual((retry.status_code, retry.json["inserted"]), (200, 2))
        self.details["retry"] = dict(status=retry.status_code, inserted=retry.json["inserted"])

    def test_CP05_postcommit_document_failure_is_recoverable_without_duplicate(self):
        """PLAN-I02: falla documental posterior a commit conserva verdad SQL; reintento idempotente."""
        bid = self.preview().json["id"]
        with patch.object(documentrepo, "update_state", side_effect=documentrepo.DocumentStoreError("Fallo derivado inyectado")):
            response = self.request("POST", f"/api/batches/{bid}/confirm")
        sql_state = self.query("SELECT estado FROM carga WHERE id=?", (bid,))[0][0]
        visible = self.client.get(f"/api/documents/{bid}").json["document"]["state"]
        retry = self.request("POST", f"/api/batches/{bid}/confirm")
        raw_state = documentrepo.report_by_batch(self.application.config["PRIVATE"], bid)["state"]
        rows = self.query("SELECT count(*) FROM calificacion WHERE instrumento LIKE 'COMP-BULK-%'")[0][0]
        confirmations = self.query("SELECT count(*) FROM evento_auditoria WHERE accion='confirmar' AND registro_id=?", (bid,))[0][0]
        self.details = dict(initial_status=response.status_code, sql_state=sql_state, api_document_state=visible,
                            retry_status=retry.status_code, idempotent=retry.json.get("idempotent"),
                            reconciled_document_state=raw_state, persisted_rows=rows, confirmation_events=confirmations)
        self.assertEqual(response.status_code, 503)
        self.assertEqual((sql_state, visible, raw_state), ("confirmada",)*3)
        self.assertEqual(retry.status_code, 200)
        self.assertTrue(retry.json["idempotent"])
        self.assertEqual(retry.json["inserted"], 2)
        self.assertEqual((rows, confirmations), (2, 1))

    def test_CP06_crud_audit_failure_rolls_back_insert_update_and_soft_delete(self):
        """PLAN-I03: falla de auditoría después de INSERT/UPDATE/baja revierte operación."""
        rid = self.create()
        view = inspect.unwrap(self.application.view_functions["update_rating"])
        def failing(original):
            def fail(*args, **kwargs):
                raise sqlite3.OperationalError("Fallo de auditoría inyectado")
            return fail
        records = []
        for method, path, payload in [("POST", "/api/ratings", dict(PAYLOAD, instrument="COMP-FAILED")),
                                      ("PUT", f"/api/ratings/{rid}", dict(PAYLOAD, amount="500", version=1)),
                                      ("DELETE", f"/api/ratings/{rid}", {"version": 1})]:
            before, audit_before = self.snapshot(), self.business_events()
            with replace_closure(view, "event", failing):
                response = self.request(method, path, payload)
            unchanged = self.snapshot() == before and self.business_events() == audit_before
            records.append(dict(method=method, status=response.status_code, unchanged=unchanged, json=response.is_json))
            self.assertIn(response.status_code, (500, 503))
            self.assertTrue(response.is_json)
            self.assertTrue(unchanged)
        self.details = dict(operations=records, fault="Errores deliberados de almacenamiento; 500/503 se espera durante inyección, no en operación válida")

    def test_CP07_required_and_calculation_failure_have_no_business_mutation(self):
        """PLAN-F02/PLAN-I03: obligatorio vacío y cálculo inválido señalan error sin escritura."""
        records = []
        for field, value in [("rating", ""), ("base", "0"), ("amount", "NaN")]:
            before, audit_before = self.snapshot(), self.business_events()
            response = self.request("POST", "/api/ratings", dict(PAYLOAD, **{field: value}))
            records.append(dict(field=field, status=response.status_code, message=response.json.get("error")))
            self.assertEqual(response.status_code, 422)
            self.assertTrue(response.json.get("error"))
            self.assertEqual(self.snapshot(), before)
            self.assertEqual(self.business_events(), audit_before)
        rid = self.create("COMP-RULE-VERSION")
        stored = self.query("SELECT c.monto,c.factor,c.regla_id,r.version FROM calificacion c JOIN regla_factor r ON r.id=c.regla_id WHERE c.id=?", (rid,))[0]
        event_after = json.loads(self.query("SELECT despues_json FROM evento_auditoria WHERE entidad='calificacion' AND accion='crear' AND registro_id=?", (rid,))[0][0])
        self.assertEqual(stored, ("250", "0.250000", 1, "DEMO-1"))
        self.assertEqual((event_after["monto"], event_after["factor"], event_after["regla_id"]), stored[:3])
        self.details = dict(cases=records, valid_write=dict(amount=stored[0], factor=stored[1], rule_id=stored[2], rule_version=stored[3], audit_matches=True))

    def test_CP08_csrf_all_mutations_missing_invalid_valid_and_audit_fields(self):
        """PLAN-S06/PLAN-F05: nueve familias CSRF y eventos de operaciones con todos sus campos."""
        event_start = self.query("SELECT coalesce(max(id),0) FROM evento_auditoria")[0][0]
        rid = self.create("COMP-CSRF-EXISTING")
        bid = self.preview(self.csv(("COMP-CSRF-BULK",))).json["id"]
        admin = self.login("admin")
        routes = [(self.client, "POST", "/api/login", dict(login="operador_a", password=demo.DEMO_PASSWORD), 200),
                  (self.client, "POST", "/api/ratings", dict(PAYLOAD, instrument="COMP-CSRF-NEW"), 201),
                  (self.client, "PUT", f"/api/ratings/{rid}", dict(PAYLOAD, instrument="COMP-CSRF-EXISTING", amount="500", version=1), 200),
                  (self.client, "DELETE", f"/api/ratings/{rid}", {"version": 2}, 200),
                  (self.client, "POST", "/api/factor/preview", {"amount": "1", "base": "2"}, 200),
                  (self.client, "POST", "/api/batches/preview", None, 200),
                  (self.client, "POST", f"/api/batches/{bid}/confirm", {}, 200),
                  (admin, "PUT", "/api/users/2", dict(role="operador", active=True, brokers=[2], version=1), 200),
                  (self.client, "POST", "/api/logout", {}, 200)]
        outcomes = []
        for client, method, path, payload, expected in routes:
            before = self.snapshot()
            rejected = []
            for bad in (None, "token-invalido-complementario"):
                if path == "/api/batches/preview":
                    response = client.post(path, data={"broker": "1", "kind": "DJ1948-DEMO", "file": (io.BytesIO(self.csv(("COMP-CSRF-PREVIEW",))), "qa.csv")},
                                           headers={} if bad is None else {"X-CSRF-Token": bad})
                else:
                    response = client.open(path, method=method, json=payload or {}, headers={} if bad is None else {"X-CSRF-Token": bad})
                rejected.append(response.status_code)
                self.assertEqual(response.status_code, 403)
                self.assertIn("CSRF", response.json["error"])
                self.assertEqual(self.snapshot(), before)
            valid = self.preview(self.csv(("COMP-CSRF-PREVIEW",)), client=client) if path == "/api/batches/preview" else self.request(method, path, payload, client=client)
            outcomes.append(dict(method=method, path=path, absent=rejected[0], invalid=rejected[1], valid=valid.status_code))
            self.assertEqual(valid.status_code, expected)
        self.details = dict(routes=outcomes, snapshots_unchanged_for_rejected=True)
        events = self.query("SELECT usuario_id,fecha,corredor_id,accion,resultado,registro_id,entidad FROM evento_auditoria "
                            "WHERE id>? AND accion IN ('crear','modificar','inactivar','prevalidar','confirmar','cambiar_perfil')", (event_start,))
        actions = set()
        for user, date, broker, action, result, record, entity in events:
            actions.add(action)
            self.assertIsNotNone(user)
            self.assertTrue(datetime.fromisoformat(date).tzinfo)
            self.assertEqual(result, "correcto")
            self.assertIsNotNone(record)
            self.assertEqual(broker is None, entity == "usuario")
        self.assertEqual(actions, {"crear", "modificar", "inactivar", "prevalidar", "confirmar", "cambiar_perfil"})
        self.details = dict(routes=outcomes, snapshots_unchanged_for_rejected=True, validated_event_actions=sorted(actions),
                            profile_event_broker="No aplica a evento de perfil; el cambio incluye asignaciones en después")

    def test_CP09_login_privacy_logout_and_old_cookie_replay(self):
        """PLAN-S02: error uniforme y bitácora privada; cookie previa al logout no reutilizable."""
        statuses, messages = [], []
        password = "CONTRASENA-FALLO-COMPLEMENTARIA"
        for name in ("operador_a", "no-existe-complementario"):
            client = self.application.test_client()
            response = self.request("POST", "/api/login", dict(login=name, password=password), client=client)
            statuses.append(response.status_code)
            messages.append(response.json["error"])
        audit_text = json.dumps(self.query("SELECT antes_json,despues_json FROM evento_auditoria WHERE accion='login_fallido'"))
        self.assertEqual(statuses, [401, 401])
        self.assertEqual(messages[0], messages[1])
        self.assertNotIn(password, audit_text)
        self.assertNotIn("no-existe-complementario", audit_text)
        previous_cookie = self.client.get_cookie("session").value
        logout = self.request("POST", "/api/logout")
        current_status = self.client.get("/api/ratings").status_code
        replay = self.application.test_client()
        replay.set_cookie("session", previous_cookie, domain="localhost")
        replay_status = replay.get("/api/ratings").status_code
        self.details = dict(login_statuses=statuses, same_error_message=messages[0] == messages[1], audit_excludes_credentials=True,
                            logout_status=logout.status_code, current_cookie_status=current_status, old_cookie_replay_status=replay_status)
        self.assertEqual((logout.status_code, current_status), (200, 401))
        self.assertEqual(replay_status, 401, "La cookie firmada anterior al cierre sigue dando acceso")
        restarted = demo.create_app(self.root / "seed", testing=True)
        restarted.config["DATABASE"] = self.application.config["DATABASE"]
        restarted.config["PRIVATE"] = self.application.config["PRIVATE"]
        after_restart = restarted.test_client()
        after_restart.set_cookie("session", previous_cookie, domain="localhost")
        restarted_status = after_restart.get("/api/ratings").status_code
        self.assertEqual(restarted_status, 401, "La revocación debe sobrevivir al reinicio con la misma clave y base")
        fresh_status = self.login().get("/api/ratings").status_code
        self.assertEqual(fresh_status, 200)
        self.details.update(old_cookie_after_restart_status=restarted_status, new_authenticated_session_status=fresh_status,
                            same_persistent_secret=restarted.secret_key == self.application.secret_key)

    def test_CP10_five_supplied_csv_examples(self):
        """PLAN-F03: cinco archivos de ejemplo por API, errores explicados y rechazo completo."""
        outcomes = []
        for filename in ["01_montos_valido.csv", "02_encabezado_invalido.csv", "03_campos_incompletos.csv", "04_duplicados.csv", "05_factores_valido.csv"]:
            before_count = self.query("SELECT count(*) FROM calificacion")[0][0]
            response = self.preview((PROTOTYPE / "ejemplos" / filename).read_bytes(), filename=filename,
                                    kind="factores-DEMO" if filename.startswith("05") else "DJ1948-DEMO")
            result = dict(file=filename, preview_status=response.status_code)
            if filename.startswith("02"):
                self.assertEqual(response.status_code, 422)
                result["message"] = response.json["error"]
            else:
                self.assertEqual(response.status_code, 200)
                result.update(total=response.json["total"], invalid=response.json["invalid"])
                confirmation = self.request("POST", f"/api/batches/{response.json['id']}/confirm")
                result["confirm_status"] = confirmation.status_code
                if filename.startswith(("01", "05")):
                    self.assertEqual(confirmation.status_code, 200)
                    self.assertEqual(self.query("SELECT count(*) FROM calificacion")[0][0]-before_count, response.json["total"])
                else:
                    self.assertGreater(response.json["invalid"], 0)
                    self.assertEqual(confirmation.status_code, 409)
                    result["errors"] = [row["errors"] for row in response.json["rows"] if row["errors"]]
            if filename.startswith(("02", "03", "04")):
                self.assertEqual(self.query("SELECT count(*) FROM calificacion")[0][0], before_count)
            outcomes.append(result)
        self.details = dict(examples=outcomes)



if __name__ == "__main__":
    unittest.main(verbosity=2)
