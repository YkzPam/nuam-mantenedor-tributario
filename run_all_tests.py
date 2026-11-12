"""Ejecuta las cinco suites del paquete v1.2 y conserva cada ejecución en evidencias/."""
from datetime import datetime, timezone
import gc
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest

CANDIDATE = Path(__file__).resolve().parent
VENDOR = CANDIDATE / "vendor"
sys.path.insert(0, str(VENDOR))
sys.path.insert(0, str(CANDIDATE))
sys.path.insert(0, str(CANDIDATE / "tests"))

class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cases = []
        self.started = {}
    def startTest(self, test):
        self.started[test.id()] = time.perf_counter()
        super().startTest(test)
    def record(self, test, status, error=None):
        row = dict(id=test.id(), description=test.shortDescription(), status=status,
                   seconds=round(time.perf_counter()-self.started.get(test.id(), time.perf_counter()), 6),
                   detail=getattr(test, "details", {}))
        if error:
            row["error"] = self._exc_info_to_string(error, test)
        self.cases.append(row)
    def addSuccess(self, test):
        self.record(test, "passed"); super().addSuccess(test)
    def addFailure(self, test, err):
        self.record(test, "failed", err); super().addFailure(test, err)
    def addError(self, test, err):
        self.record(test, "error", err); super().addError(test, err)
    def stopTest(self, test):
        super().stopTest(test); gc.collect()


groups = []
for module_name in ["test_demo", "test_ui_revision", "test_complementarias", "test_v11", "test_v12"]:
    module = __import__(module_name)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
    groups.append(dict(suite=module_name, tests=result.testsRun,
                       passed=sum(row["status"] == "passed" for row in result.cases),
                       failed=len(result.failures), errors=len(result.errors), cases=result.cases,
                       metrics=getattr(module, "METRICS", {})))

sources = [CANDIDATE / filename for filename in ["app.py", "schema.sql", "domain.py", "documentrepo.py",
           "templates/index.html", "static/app.js", "static/style.css", "tests/test_demo.py",
           "tests/test_ui_revision.py", "tests/test_complementarias.py", "tests/test_v11.py", "tests/test_v12.py", "wsgi.py",
           "pruebas_estres.py", "run_all_tests.py"]]
report = dict(executed_utc=datetime.now(timezone.utc).isoformat(),
              tests=sum(group["tests"] for group in groups), passed=sum(group["passed"] for group in groups),
              failed=sum(group["failed"] for group in groups), errors=sum(group["errors"] for group in groups),
              suites=groups, source_directory=str(CANDIDATE),
              predecessor_zip_sha256="c75bcd6788e7997e0aad45a1f4a48cea203a7b187823579c2f7d84f2c817836e",
              source_sha256={str(path.relative_to(CANDIDATE)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
              python=sys.version, executable=sys.executable, dependencies=str(VENDOR), isolated=True,
              corrections=["Ownership de archivos registrado antes de escribir; rollback de preview limpia todos los archivos creados.",
                           "Logout persiste SHA-256 del identificador aleatorio de sesión en evento de auditoría; la cookie anterior se rechaza incluso tras reiniciar con misma clave/base.",
                           "Índice parcial para hashes revocados sin tabla ni columna nueva; errores de almacenamiento controlados con 503 sin publicar rutas/SQL.",
                           "Los campos textuales obligatorios rechazan valores nulos, booleanos, colecciones y tipos incompatibles sin convertirlos a texto.",
                           "La confirmación exitosa sustituye el estado pendiente del lote visible, conserva el conteo confirmado y deshabilita una nueva confirmación; una respuesta anterior no sobrescribe la previsualización de otro lote.",
                           "v1.1: el atributo pattern del instrumento escapa el guion y vuelve a ser válido en Chrome (D3).",
                           "v1.1: registro operativo en data/logs/operacion.log con método, ruta declarada, estado, duración y perfil, sin cuerpo, consulta ni credenciales.",
                           "v1.1: NUAM_ROLES_FACTOR_MANUAL permite limitar el ingreso manual de factores; sin la variable rige la matriz de la Unidad 2.",
                           "v1.1: wsgi.py para servir con Waitress e ícono embebido que evita la solicitud 404 a /favicon.ico.",
                           "v1.1: SQLite en modo WAL; con 100 clientes en proceso el P95 de guardado bajó de 6,97 s con 31 respuestas 503 a 2,20 s sin 5xx (pruebas_estres.py).",
                           "v1.2: regla DEMO-2, definida por el equipo y pendiente de validación de NUAM: catálogo de instrumentos por mercado; un inscrito debe existir habilitado y un no inscrito nuevo se agrega con evento de bitácora.",
                           "v1.2: regla DEMO-3, definida por el equipo y pendiente de validación de NUAM: el archivo de Bolsa, cargado solo por el supervisor, reemplaza el registro del corredor y la bitácora conserva los valores anteriores.",
                           "v1.2: una base anterior al esquema 2 se respalda completa en data/respaldo_v1_<fecha>/ antes de crear el esquema nuevo."],
              limits="Ejecución técnica local con bases/archivos temporales. No modifica base visible, fuente ZIP ni Downloads. No prueba infraestructura NUAM, dispositivos físicos ni acciones/comentarios humanos. Fallos intermedios se inyectan deliberadamente.")
destination = CANDIDATE / "evidencias" / ("ejecucion_completa_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f"))
destination.mkdir(parents=True, exist_ok=False)
(destination / "resultados_corregidos.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
lines = ["# Pruebas del paquete de la Unidad 3 (v1.2)", "", f"Fecha UTC: {report['executed_utc']}", "",
         f"Total real: {report['passed']}/{report['tests']} aprobadas, {report['failed']} fallas, {report['errors']} errores.", "",
         "| Suite | Casos | Aprobados | Fallas | Errores |", "|---|---:|---:|---:|---:|"]
for group in groups:
    lines.append(f"| {group['suite']} | {group['tests']} | {group['passed']} | {group['failed']} | {group['errors']} |")
lines += ["", "## Correcciones verificadas", ""] + report["corrections"] + ["", "## Casos complementarios y de regresión v1.1 y v1.2", "",
          "| Caso | Resultado | Comprobación |", "|---|---|---|"]
for case in [case for group in groups[2:] for case in group["cases"]]:
    lines.append(f"| {case['id'].rsplit('.',1)[-1]} | {case['status']} | {case['description']} |")
lines += ["", "## Límites de la evidencia", "", report["limits"], "",
          "Las mediciones y detalles de cada caso se conservan en resultados_corregidos.json. La suite de 40 casos conserva su P01 de consultas; CP01 agrega 20 escrituras simultáneas medidas separadamente. La prueba de estrés sostenida se ejecuta aparte con pruebas_estres.py."]
(destination / "resultados_corregidos.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
print(json.dumps({"tests": report["tests"], "passed": report["passed"], "failed": report["failed"], "errors": report["errors"], "report": str(destination)}, ensure_ascii=False))
sys.exit(0 if not report["failed"] and not report["errors"] else 1)
