"""Prueba de estrés sostenida del prototipo (fuera de las suites unitarias).

Fases:
  1. Carga mixta sostenida por niveles de clientes concurrentes (por defecto 20, 50 y 100),
     cada uno con su propia sesión: 80 % consultas y 20 % guardados durante N segundos.
  2. Lotes sucesivos de 1.000 filas (previsualizar + confirmar) con memoria medida por lote.
  3. Integridad: filas persistidas contra respuestas 201 y cadena HMAC de la bitácora.

Modos:
  python pruebas_estres.py                      -> aplicación en proceso con base temporal
  python pruebas_estres.py --url http://127.0.0.1:8765
                                                -> servidor en ejecución (Waitress o app.py).
     Usar una carpeta de datos desechable (NUAM_DATA_DIR): la prueba crea registros ficticios.

Criterios del plan de pruebas: P95 de hasta 3 s por operación y cero respuestas HTTP 5xx.
Los resultados se guardan en evidencias/estres_<fecha>/ (JSON y Markdown).
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gc
import http.cookiejar
import io
import json
import math
from pathlib import Path
import platform
import random
import sqlite3
import sys
import tempfile
from threading import Barrier
import time
import urllib.error
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from domain import CSV_COLUMNS  # noqa: E402

PASSWORD = "Demo2026!"
USERS = [("operador_a", 1), ("operador_b", 2), ("supervisor", 1), ("supervisor", 2)]
LIMIT_SECONDS = 3.0


def resident_mib():
    """Memoria residente actual del proceso, sin instrumentar las asignaciones.

    Linux: /proc/self/statm. Windows: GetProcessMemoryInfo. En otros sistemas se
    informa el máximo de getrusage, que solo puede crecer.
    """
    try:
        if sys.platform.startswith("linux"):
            import os
            pages = int(Path("/proc/self/statm").read_text().split()[1])
            return round(pages * os.sysconf("SC_PAGE_SIZE") / 2**20, 1), "residente actual"
        if sys.platform == "win32":
            import ctypes
            from ctypes import wintypes

            class Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
            counters = Counters()
            counters.cb = ctypes.sizeof(Counters)
            process = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.psapi.GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb)
            return round(counters.WorkingSetSize / 2**20, 1), "residente actual"
        import resource
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return round(peak / (2**20 if sys.platform == "darwin" else 2**10), 1), "máximo del proceso"
    except Exception:
        return None, "no disponible"


def percentile(values, fraction):
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)] if ordered else None


class InProcessClient:
    def __init__(self, application):
        self.client = application.test_client()
        self.csrf = None

    def get(self, path):
        response = self.client.get(path)
        return response.status_code, response.get_json(silent=True)

    def post_json(self, path, payload):
        response = self.client.post(path, json=payload, headers={"X-CSRF-Token": self.csrf or ""})
        return response.status_code, response.get_json(silent=True)

    def post_file(self, path, fields, filename, content):
        data = dict(fields, file=(io.BytesIO(content), filename))
        response = self.client.post(path, data=data, headers={"X-CSRF-Token": self.csrf or ""})
        return response.status_code, response.get_json(silent=True)


class HttpClient:
    def __init__(self, base_url):
        self.base = base_url.rstrip("/")
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.csrf = None

    def _send(self, request):
        try:
            with self.opener.open(request, timeout=60) as response:
                return response.status, json.loads(response.read() or b"null")
        except urllib.error.HTTPError as error:
            body = error.read()
            try:
                return error.code, json.loads(body or b"null")
            except ValueError:
                return error.code, None

    def get(self, path):
        return self._send(urllib.request.Request(self.base + path))

    def post_json(self, path, payload):
        request = urllib.request.Request(self.base + path, data=json.dumps(payload).encode(), method="POST",
                                         headers={"Content-Type": "application/json", "X-CSRF-Token": self.csrf or ""})
        return self._send(request)

    def post_file(self, path, fields, filename, content):
        boundary = uuid.uuid4().hex
        parts = []
        for name, value in fields.items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
        parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
                      "Content-Type: text/csv\r\n\r\n").encode() + content + b"\r\n")
        parts.append(f"--{boundary}--\r\n".encode())
        request = urllib.request.Request(self.base + path, data=b"".join(parts), method="POST",
                                         headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                                                  "X-CSRF-Token": self.csrf or ""})
        return self._send(request)


def login(client, user):
    status, body = client.get("/api/me")
    client.csrf = body["csrf"]
    status, _ = client.post_json("/api/login", dict(login=user, password=PASSWORD))
    if status != 200:
        raise RuntimeError(f"No fue posible iniciar sesión como {user}: HTTP {status}")
    client.csrf = client.get("/api/me")[1]["csrf"]
    return client


def sustained_level(sessions, level, seconds, run_tag):
    barrier = Barrier(level)

    def worker(index):
        client, broker = sessions[index]
        rng = random.Random(f"{run_tag}-{level}-{index}")
        records = []
        barrier.wait()
        deadline = time.perf_counter() + seconds
        counter = 0
        while time.perf_counter() < deadline:
            if rng.random() < 0.8:
                filters = rng.choice(["", "&market=SCL", "&period=2026-10", "&q=DEMO", "&origin=manual", "&page=2"])
                started = time.perf_counter()
                status, _ = client.get(f"/api/ratings?broker={broker}{filters}")
                records.append(("consulta", time.perf_counter() - started, status))
            else:
                counter += 1
                payload = dict(broker=broker, market="SCL", period="2026-10",
                               instrument=f"ESTRES-{run_tag}-{level}-{index}-{counter}"[:40],
                               rating="Estres demo", registered="0", mode="monto", amount="250", base="1000")
                started = time.perf_counter()
                status, _ = client.post_json("/api/ratings", payload)
                records.append(("guardado", time.perf_counter() - started, status))
        return records

    wall = time.perf_counter()
    with ThreadPoolExecutor(max_workers=level) as pool:
        results = [record for chunk in pool.map(worker, range(level)) for record in chunk]
    wall = time.perf_counter() - wall
    summary = dict(clientes=level, segundos_configurados=seconds, segundos_reales=round(wall, 3),
                   solicitudes=len(results), por_segundo=round(len(results) / wall, 2), operaciones={})
    for operation in ("consulta", "guardado"):
        times = [r[1] for r in results if r[0] == operation]
        codes = {}
        for r in results:
            if r[0] == operation:
                codes[str(r[2])] = codes.get(str(r[2]), 0) + 1
        summary["operaciones"][operation] = dict(
            total=len(times), p50=round(percentile(times, .50), 4) if times else None,
            p95=round(percentile(times, .95), 4) if times else None,
            p99=round(percentile(times, .99), 4) if times else None,
            maximo=round(max(times), 4) if times else None, codigos=codes,
            errores_5xx=sum(v for k, v in codes.items() if k.startswith("5")))
    summary["guardados_201"] = summary["operaciones"]["guardado"]["codigos"].get("201", 0)
    summary["cumple_p95"] = all((op["p95"] or 0) <= LIMIT_SECONDS for op in summary["operaciones"].values())
    summary["cumple_sin_5xx"] = all(op["errores_5xx"] == 0 for op in summary["operaciones"].values())
    return summary


def successive_batches(client, broker, batches, run_tag, measure_memory):
    rows_out = []
    for number in range(1, batches + 1):
        rows = [f"SCL,2026-10,L{run_tag}-{number}-{n},Lote estres,monto,1,2,,1" for n in range(1000)]
        content = (",".join(CSV_COLUMNS) + "\n" + "\n".join(rows) + "\n").encode()
        started = time.perf_counter()
        status_preview, preview = client.post_file("/api/batches/preview", {"broker": str(broker), "kind": "DJ1948-DEMO"},
                                                   f"lote_{number}.csv", content)
        preview_seconds = time.perf_counter() - started
        status_confirm, confirm = (None, None)
        confirm_seconds = None
        if status_preview == 200 and preview.get("can_confirm"):
            started = time.perf_counter()
            status_confirm, confirm = client.post_json(f"/api/batches/{preview['id']}/confirm", {})
            confirm_seconds = time.perf_counter() - started
        started = time.perf_counter()
        status_query, query = client.get(f"/api/ratings?broker={broker}")
        query_seconds = time.perf_counter() - started
        row = dict(lote=number, filas=1000, previsualizacion_http=status_preview,
                   previsualizacion_s=round(preview_seconds, 4), confirmacion_http=status_confirm,
                   confirmacion_s=round(confirm_seconds, 4) if confirm_seconds is not None else None,
                   insertadas=(confirm or {}).get("inserted"), consulta_posterior_s=round(query_seconds, 4),
                   total_corredor=(query or {}).get("total"))
        if measure_memory:
            gc.collect()
            row["memoria_mib"], row["tipo_memoria"] = resident_mib()
        rows_out.append(row)
        print(f"  lote {number}: previsualización {row['previsualizacion_s']} s, "
              f"confirmación {row['confirmacion_s']} s, HTTP {status_preview}/{status_confirm}", flush=True)
    return rows_out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", help="URL de un servidor en ejecución; sin ella se usa la aplicación en proceso")
    parser.add_argument("--niveles", default="20,50,100", help="clientes concurrentes por nivel (separados por coma)")
    parser.add_argument("--segundos", type=float, default=30, help="duración de cada nivel de carga sostenida")
    parser.add_argument("--lotes", type=int, default=10, help="cantidad de lotes sucesivos de 1.000 filas")
    args = parser.parse_args()
    levels = [int(value) for value in args.niveles.split(",") if value.strip()]
    run_tag = datetime.now(timezone.utc).strftime("%H%M%S")
    workspace = None
    if args.url:
        make_client = lambda: HttpClient(args.url)  # noqa: E731
        mode = f"HTTP contra {args.url}"
        database = None
    else:
        import app as demo
        workspace = tempfile.TemporaryDirectory(prefix="nuam-estres-")
        application = demo.create_app(Path(workspace.name) / "data", testing=True)
        make_client = lambda: InProcessClient(application)  # noqa: E731
        mode = "aplicación en proceso (Flask test_client) con SQLite temporal"
        database = application.config["DATABASE"]

    print(f"Modo: {mode}. Iniciando {max(levels)} sesiones...", flush=True)
    started = time.perf_counter()
    sessions = []
    for index in range(max(levels)):
        user, broker = USERS[index % len(USERS)]
        sessions.append((login(make_client(), user), broker))
    login_seconds = time.perf_counter() - started

    report = dict(ejecutado_utc=datetime.now(timezone.utc).isoformat(), modo=mode, python=sys.version.split()[0],
                  plataforma=platform.platform(), criterio_p95_s=LIMIT_SECONDS, sesiones=len(sessions),
                  inicio_sesiones_s=round(login_seconds, 2), niveles=[], lotes=[])
    for level in levels:
        print(f"Nivel {level} clientes durante {args.segundos:g} s...", flush=True)
        summary = sustained_level(sessions, level, args.segundos, run_tag)
        report["niveles"].append(summary)
        ops = summary["operaciones"]
        print(f"  {summary['solicitudes']} solicitudes; P95 consulta {ops['consulta']['p95']} s, "
              f"P95 guardado {ops['guardado']['p95']} s, 5xx {ops['consulta']['errores_5xx'] + ops['guardado']['errores_5xx']}",
              flush=True)

    print(f"Lotes sucesivos: {args.lotes} x 1.000 filas...", flush=True)
    batch_client, batch_broker = sessions[0]
    report["lotes"] = successive_batches(batch_client, batch_broker, args.lotes, run_tag, measure_memory=not args.url)

    expected_saved = sum(level["guardados_201"] for level in report["niveles"])
    expected_batch = sum(row["insertadas"] or 0 for row in report["lotes"])
    if database:
        with sqlite3.connect(database) as conn:
            saved = conn.execute("SELECT count(*) FROM calificacion WHERE instrumento LIKE ?", (f"ESTRES-{run_tag}-%",)).fetchone()[0]
            batched = conn.execute("SELECT count(*) FROM calificacion WHERE instrumento LIKE ?", (f"L{run_tag}-%",)).fetchone()[0]
            events = conn.execute("SELECT count(*) FROM evento_auditoria").fetchone()[0]
    else:
        saved = sum(client.get(f"/api/ratings?broker={broker}&q=ESTRES-{run_tag}-")[1]["total"]
                    for client, broker in {broker: (client, broker) for client, broker in sessions}.values())
        batched = batch_client.get(f"/api/ratings?broker={batch_broker}&q=L{run_tag}-")[1]["total"]
        events = None
    started = time.perf_counter()
    status, audit = sessions[0][0].get("/api/audit")
    audit_seconds = round(time.perf_counter() - started, 4)
    report["integridad"] = dict(guardados_201=expected_saved, guardados_persistidos=saved, verificacion_bitacora_s=audit_seconds,
                                filas_lote_confirmadas=expected_batch, filas_lote_persistidas=batched,
                                eventos_auditoria=events, cadena_hmac_valida=bool(audit and audit.get("integrity")))
    report["cumple"] = (all(level["cumple_p95"] and level["cumple_sin_5xx"] for level in report["niveles"])
                        and all(row["previsualizacion_http"] == 200 and row["confirmacion_http"] == 200 for row in report["lotes"])
                        and saved == expected_saved and batched == expected_batch
                        and report["integridad"]["cadena_hmac_valida"])

    destination = ROOT / "evidencias" / ("estres_" + datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "resultados_estres.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Prueba de estrés sostenida", "", f"Fecha UTC: {report['ejecutado_utc']}", f"Modo: {mode}",
             f"Python {report['python']} · {report['plataforma']}", "",
             "| Clientes | Segundos | Solicitudes | Sol./s | P95 consulta (s) | P95 guardado (s) | Máx. guardado (s) | 5xx |",
             "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for level in report["niveles"]:
        ops = level["operaciones"]
        lines.append(f"| {level['clientes']} | {level['segundos_reales']} | {level['solicitudes']} | {level['por_segundo']} | "
                     f"{ops['consulta']['p95']} | {ops['guardado']['p95']} | {ops['guardado']['maximo']} | "
                     f"{ops['consulta']['errores_5xx'] + ops['guardado']['errores_5xx']} |")
    lines += ["", "| Lote | Previsualización (s) | Confirmación (s) | Consulta posterior (s) | Filas del corredor | Memoria del proceso (MiB) |",
              "|---:|---:|---:|---:|---:|---:|"]
    for row in report["lotes"]:
        lines.append(f"| {row['lote']} | {row['previsualizacion_s']} | {row['confirmacion_s']} | {row['consulta_posterior_s']} | "
                     f"{row['total_corredor']} | {row.get('memoria_mib', '-')} |")
    lines += ["", "Integridad: " + json.dumps(report["integridad"], ensure_ascii=False), "",
              f"Resultado global: {'cumple' if report['cumple'] else 'no cumple'} los criterios (P95 <= 3 s, sin 5xx, persistencia y cadena HMAC).",
              "", "Límites: datos ficticios, un solo equipo y SQLite local; no reemplaza una prueba en infraestructura de NUAM."]
    (destination / "resultados_estres.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(dict(cumple=report["cumple"], informe=str(destination)), ensure_ascii=False))
    if workspace:
        workspace.cleanup()
    return 0 if report["cumple"] else 1


if __name__ == "__main__":
    sys.exit(main())
