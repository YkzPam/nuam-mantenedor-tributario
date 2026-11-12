"""Prototipo académico local: únicamente datos ficticios, sin integración NUAM."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'vendor'))
import csv
import hashlib
import hmac
import io
import json
import logging
import os
import re
import secrets
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, abort, g, jsonify, render_template, request, session, send_file
from werkzeug.exceptions import HTTPException
from werkzeug.security import generate_password_hash, check_password_hash
from domain import ValidationError, validate_rating, business_key, parse_csv, CSV_COLUMNS, MAX_FILE_BYTES, factor_demo
import documentrepo

DEMO_PASSWORD = 'Demo2026!'
RATE_FAILURES = {}
SCHEMA_VERSION = 2
BOLSA = 'bolsa-DEMO'
CORREDOR_KINDS = ('DJ1948-DEMO', 'factores-DEMO')
BATCH_KINDS = CORREDOR_KINDS + (BOLSA,)
# Reglas DEMO-2 y DEMO-3 (v1.2): definidas por el equipo para la demostración, pendientes de validación de NUAM.
CATALOG_RULE = ('DEMO-2: un instrumento inscrito debe existir habilitado en el catálogo del mercado; '
                'un no inscrito fuera del catálogo se admite y, si figura en él, debe estar habilitado. No aprobada por NUAM.')
# Condición DEMO-2 evaluada dentro de la misma sentencia de escritura: sin consultas extra en el guardado normal.
CATALOG_GUARD = ("NOT EXISTS (SELECT 1 FROM instrumento i WHERE i.mercado=? AND i.codigo=? AND (i.habilitado=0 OR i.inscrito<>?)) "
                 "AND (?=0 OR EXISTS (SELECT 1 FROM instrumento i WHERE i.mercado=? AND i.codigo=?))")

def catalog_guard_params(data):
    return (data['mercado'],data['instrumento'],data['inscrito'],data['inscrito'],data['mercado'],data['instrumento'])

class CatalogConflict(Exception):
    """La escritura no se hizo porque el instrumento no cumple la regla DEMO-2."""

CATALOG_WRITE_MESSAGE = ('El catálogo de instrumentos cambió durante la operación (regla DEMO-2). '
                         'No se guardaron cambios; volver a intentar.')
CATALOG_CHANGED_MESSAGE = ('El catálogo de instrumentos cambió después de la previsualización (regla DEMO-2). '
                           'La carga no se guardó; volver a validar.')
BOLSA_RULE = ('DEMO-3: la información informada por Bolsa prevalece sobre la del corredor; '
              'el registro anterior queda en la bitácora. No aprobada por NUAM.')
BOLSA_PRIORITY_MESSAGE = ('Existe un registro informado por Bolsa con la misma llave provisional; '
                          'prevalece sobre la información del corredor (regla DEMO-3).')
CATALOG_SEED = [('SCL','DEMO-ALFA',1,1),('SCL','DEMO-BETA',1,1),('SCL','DEMO-NO-INSCRITO',0,1),
                ('SCL','DEMO-SUSPENDIDO',1,0),('SCL','DEMO-DUPLICADO',1,1),('SCL','DEMO-INCOMPLETO',1,1),
                ('COL','DEMO-FILE-2',1,1),('LIM','DEMO-FACTOR-1',0,1)]

def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',',':'))

class OperationLogHandler(logging.Handler):
    """Registro operativo en líneas JSON; rota a los 5 MB y conserva tres archivos anteriores.

    El archivo se abre y se cierra en cada escritura para no dejar bloqueadas
    carpetas temporales en Windows; el candado del handler ordena los hilos.
    """
    def __init__(self, path, max_bytes=5_000_000, backups=3):
        super().__init__()
        self.path = Path(path)
        self.max_bytes = max_bytes
        self.backups = backups
    def rotate(self):
        for number in range(self.backups - 1, 0, -1):
            older = self.path.with_name(f'{self.path.name}.{number}')
            if older.exists():
                os.replace(older, self.path.with_name(f'{self.path.name}.{number + 1}'))
        os.replace(self.path, self.path.with_name(self.path.name + '.1'))
    def emit(self, record):
        try:
            line = self.format(record) + '\n'
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if self.path.exists() and self.path.stat().st_size > self.max_bytes:
                self.rotate()
            with open(self.path, 'a', encoding='utf-8') as handle:
                handle.write(line)
        except Exception:
            self.handleError(record)

FACTOR_ROLES_ALLOWED = ('operador', 'supervisor')

def factor_roles_from_env():
    """Perfiles que pueden ingresar factores manualmente (NUAM_ROLES_FACTOR_MANUAL).

    Sin la variable se conserva la matriz de perfiles de la Unidad 2: operador y supervisor.
    """
    raw = os.environ.get('NUAM_ROLES_FACTOR_MANUAL')
    if raw is None:
        return FACTOR_ROLES_ALLOWED
    roles = tuple(dict.fromkeys(item.strip() for item in raw.split(',') if item.strip()))
    if not set(roles) <= set(FACTOR_ROLES_ALLOWED):
        raise ValueError('NUAM_ROLES_FACTOR_MANUAL solo admite operador y/o supervisor.')
    return roles

def backup_previous_schema(data_dir):
    """Respalda una base anterior a la v1.2 antes de crear el esquema nuevo.

    SQLite no permite cambiar restricciones CHECK con ALTER TABLE. Como la demostración
    solo contiene datos ficticios, la base y los archivos privados anteriores se mueven
    completos a data/respaldo_v1_<fecha>/ y la aplicación crea una base nueva.
    """
    database=data_dir/'demo.sqlite3'
    if not database.exists(): return None
    with closing(sqlite3.connect(database)) as conn:
        version=conn.execute('PRAGMA user_version').fetchone()[0]
        tables=conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    if version>=SCHEMA_VERSION or not tables: return None
    backup=data_dir/('respaldo_v1_'+datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f'))
    backup.mkdir()
    for suffix in ('','-wal','-shm'):
        source=data_dir/('demo.sqlite3'+suffix)
        if source.exists(): os.replace(source,backup/source.name)
    if (data_dir/'private').exists(): os.replace(data_dir/'private',backup/'private')
    return backup

def create_app(data_dir=None, testing=False):
    data_dir=Path(data_dir or ROOT/'data')
    data_dir.mkdir(parents=True,exist_ok=True)
    schema_backup=backup_previous_schema(data_dir)
    private=data_dir/'private'; private.mkdir(exist_ok=True)
    key_file=data_dir/'local-secret.key'
    if not key_file.exists():
        # Secret generated per installation, never hard-coded or shipped in source.
        key_file.write_bytes(secrets.token_bytes(32))
    app=Flask(__name__)
    app.config.update(SECRET_KEY=key_file.read_bytes(), TESTING=testing, DATABASE=str(data_dir/'demo.sqlite3'),
        PRIVATE=str(private), MAX_CONTENT_LENGTH=MAX_FILE_BYTES+10_000, SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Strict', SESSION_COOKIE_SECURE=False, TRUSTED_HOSTS=['127.0.0.1','localhost'],
        PERMANENT_SESSION_LIFETIME=1800, SESSION_REFRESH_EACH_REQUEST=False,
        OPERATION_LOG=str(data_dir/'logs'/'operacion.log'), ROLES_FACTOR_MANUAL=factor_roles_from_env(),
        SCHEMA_BACKUP=str(schema_backup) if schema_backup else None)
    # Logger propio de cada instancia: no se registra globalmente ni propaga a otros handlers.
    oplog=logging.Logger('nuam.operacion', logging.INFO)
    oplog.addHandler(OperationLogHandler(app.config['OPERATION_LOG']))
    app.oplog=oplog
    if schema_backup:
        oplog.warning(canonical(dict(fecha=stamp(),evento='respaldo_esquema_anterior',carpeta=schema_backup.name)))
        if not testing: print(f'Base anterior a la v1.2 respaldada en {schema_backup}; se creó una base nueva con datos ficticios.')

    def db():
        if 'db' not in g:
            g.db=sqlite3.connect(app.config['DATABASE'],timeout=10)
            g.db.row_factory=sqlite3.Row
            g.db.execute('PRAGMA foreign_keys=ON')
        return g.db

    @app.teardown_appcontext
    def close_db(error=None):
        conn=g.pop('db',None)
        if conn is not None: conn.close()

    def event(conn, action, entity='seguridad', record_id=None, broker=None, before=None, after=None, result='correcto', uid=None):
        if not conn.in_transaction: conn.execute('BEGIN IMMEDIATE')
        uid = uid if uid is not None else (g.user['id'] if getattr(g,'user',None) else None)
        last=conn.execute('SELECT hash_evento FROM evento_auditoria ORDER BY id DESC LIMIT 1').fetchone()
        previous=last[0] if last else '0'*64
        values=dict(usuario_id=uid,corredor_id=broker,entidad=entity,registro_id=record_id,accion=action,
                    fecha=stamp(),antes_json=canonical(before) if before is not None else None,
                    despues_json=canonical(after) if after is not None else None,resultado=result,hash_anterior=previous)
        digest=hmac.new(app.secret_key,canonical(values).encode(),hashlib.sha256).hexdigest()
        conn.execute('INSERT INTO evento_auditoria (usuario_id,corredor_id,entidad,registro_id,accion,fecha,antes_json,despues_json,resultado,hash_anterior,hash_evento) VALUES (?,?,?,?,?,?,?,?,?,?,?)',tuple(values.values())+(digest,))

    def security(action,result='rechazado'):
        conn=db()
        with conn: event(conn,action,result=result)

    def need_user(roles=None):
        def deco(fn):
            @wraps(fn)
            def wrapper(*args,**kwargs):
                if not g.user: abort(401,description='La sesión terminó. Iniciar sesión nuevamente.')
                if roles and g.user['rol'] not in roles:
                    security('permiso_denegado')
                    abort(403,description='El perfil no tiene permiso para esta operación.')
                return fn(*args,**kwargs)
            return wrapper
        return deco

    def allowed_brokers():
        if not g.user: return []
        return [r[0] for r in db().execute('SELECT corredor_id FROM usuario_corredor WHERE usuario_id=?',(g.user['id'],))]

    def json_payload():
        payload=request.get_json(silent=True)
        if not isinstance(payload,dict): abort(400,description='Enviar un objeto JSON válido.')
        return payload

    def require_broker(broker):
        try: broker=int(broker)
        except (ValueError,TypeError): abort(400,description='Corredor inválido.')
        if broker not in allowed_brokers():
            security('corredor_denegado')
            abort(403,description='No se autoriza el acceso al recurso solicitado.')
        return broker

    def rating_object(rid):
        row=db().execute('SELECT * FROM calificacion WHERE id=?',(rid,)).fetchone()
        if not row or row['corredor_id'] not in allowed_brokers():
            security('objeto_no_disponible')
            abort(404,description='Recurso no disponible.')
        return dict(row)

    @app.before_request
    def start_timer():
        g.started=time.perf_counter()

    @app.before_request
    def session_and_csrf():
        g.user=None
        uid=session.get('uid')
        if uid:
            session_id=session.get('sid')
            session_hash=hashlib.sha256(session_id.encode()).hexdigest() if isinstance(session_id,str) else None
            revoked=session_hash and db().execute(
                "SELECT 1 FROM evento_auditoria WHERE accion='logout' AND usuario_id=? AND json_extract(despues_json,'$.session_hash')=? LIMIT 1",
                (uid,session_hash)).fetchone()
            if not session_hash or revoked or time.time()-session.get('last',0)>1800:
                session.clear()
            else:
                user=db().execute('SELECT u.id,u.nombre,u.login,u.activo,r.nombre rol FROM usuario u JOIN rol r ON r.id=u.rol_id WHERE u.id=?',(uid,)).fetchone()
                if user and user['activo']:
                    g.user=dict(user); session['last']=time.time()
                else: session.clear()
        if 'csrf' not in session: session['csrf']=secrets.token_urlsafe(32)
        if request.method in ('POST','PUT','PATCH','DELETE'):
            token=request.headers.get('X-CSRF-Token') or request.form.get('csrf','')
            if not token or not hmac.compare_digest(token,str(session['csrf'])):
                security('csrf_rechazado')
                abort(403,description='Solicitud sin token CSRF válido. Recargar la página.')

    @app.after_request
    def security_headers(response):
        response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['X-Content-Type-Options']='nosniff'
        response.headers['X-Frame-Options']='DENY'
        response.headers['Referrer-Policy']='same-origin'
        if request.path!='/static': response.headers['Cache-Control']='no-store'
        return response

    @app.after_request
    def operation_log(response):
        # Solo metadatos: ruta declarada (sin identificadores ni texto de búsqueda),
        # método, estado, duración y perfil. Nunca cuerpo, cookies, tokens ni contraseñas.
        started=g.get('started')
        user=getattr(g,'user',None)
        app.oplog.info(canonical(dict(fecha=stamp(),metodo=request.method,
            ruta=request.url_rule.rule if request.url_rule else 'sin_ruta',estado=response.status_code,
            ms=round((time.perf_counter()-started)*1000,2) if started is not None else None,
            rol=user['rol'] if user else None)))
        return response

    def require_factor_permission(mode):
        if mode=='factor' and g.user['rol'] not in app.config['ROLES_FACTOR_MANUAL']:
            security('factor_manual_denegado')
            abort(403,description='El perfil no está autorizado para ingresar factores manualmente.')

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error=error.description),error.code
        return render_template('error.html',message=error.description),error.code

    @app.errorhandler(ValidationError)
    def invalid(error): return jsonify(error=str(error)),422

    @app.errorhandler(documentrepo.DocumentStoreError)
    def documents_unavailable(error):
        return jsonify(error='Repositorio documental temporalmente no disponible. Los datos operativos se conservan en SQLite.'),503

    @app.errorhandler(OSError)
    @app.errorhandler(sqlite3.OperationalError)
    def storage_unavailable(error):
        # Do not expose paths, SQL, credentials or injected exception details.
        return jsonify(error='Almacenamiento temporalmente no disponible. La operación no pudo completarse; volver a intentar.'),503

    @app.errorhandler(CatalogConflict)
    def catalog_conflict(error):
        return jsonify(error=CATALOG_WRITE_MESSAGE),409

    @app.errorhandler(sqlite3.IntegrityError)
    def constraint(error):
        # No SQL or internal names in user-facing responses.
        return jsonify(error='El registro está duplicado o incumple una referencia válida.'),409

    @app.route('/')
    def index():
        factor_manual=bool(g.user) and g.user['rol'] in app.config['ROLES_FACTOR_MANUAL']
        return render_template('index.html',user=g.user,csrf=session['csrf'],factor_manual=factor_manual,
                               bolsa_upload=bool(g.user) and g.user['rol']=='supervisor')

    @app.get('/api/me')
    def me():
        brokers=[]
        if g.user:
            ids=allowed_brokers()
            if ids: brokers=[dict(x) for x in db().execute('SELECT * FROM corredor WHERE id IN ('+','.join('?'*len(ids))+')',ids)]
        return jsonify(user=g.user,brokers=brokers,csrf=session['csrf'],demo=True,rule='DEMO-1: monto/base; 6 decimales; HALF_UP; no aprobada por NUAM',
                       rules=dict(catalog=CATALOG_RULE,bolsa=BOLSA_RULE))

    @app.post('/api/login')
    def login():
        payload=json_payload()
        login=str(payload.get('login',''))[:80]
        password=str(payload.get('password',''))[:200]
        key=(request.remote_addr,login)
        failures=[v for v in RATE_FAILURES.get(key,[]) if time.time()-v<60]
        RATE_FAILURES[key]=failures
        if len(failures)>=5:
            return jsonify(error='Acceso temporalmente bloqueado. Esperar 60 segundos.'),429
        row=db().execute('SELECT * FROM usuario WHERE login=? AND activo=1',(login,)).fetchone()
        good=check_password_hash(row['password_hash'],password) if row else check_password_hash(app.config['DUMMY_HASH'],password)
        if not good:
            failures.append(time.time()); security('login_fallido')
            return jsonify(error='Credenciales no válidas.'),401
        session.clear(); session.update(uid=row['id'],sid=secrets.token_urlsafe(32),csrf=secrets.token_urlsafe(32),last=time.time())
        with db(): event(db(),'login',uid=row['id'])
        RATE_FAILURES.pop(key,None)
        return jsonify(ok=True)

    @app.post('/api/logout')
    @need_user()
    def logout():
        # A captured signed cookie is revoked persistently, including after
        # restarting the local process. Only its random identifier hash is logged.
        session_hash=hashlib.sha256(session['sid'].encode()).hexdigest()
        with db(): event(db(),'logout',after=dict(session_hash=session_hash))
        session.clear()
        return jsonify(ok=True)

    @app.get('/api/ratings')
    @need_user(('operador','supervisor'))
    def ratings():
        ids=allowed_brokers()
        if not ids: return jsonify(items=[],total=0,page=1)
        where=['c.activo=1','c.corredor_id IN ('+','.join('?'*len(ids))+')']; params=list(ids)
        for arg,col in [('broker','corredor_id'),('market','mercado'),('period','periodo'),('origin','origen')]:
            if request.args.get(arg):
                value=request.args[arg]
                if arg=='broker': value=require_broker(value)
                where.append('c.'+col+'=?'); params.append(value)
        if request.args.get('q'):
            where.append('(c.instrumento LIKE ? OR c.calificacion LIKE ?)')
            params.extend(['%'+request.args['q'][:80]+'%']*2)
        try: page=max(1,min(int(request.args.get('page',1)),100000))
        except ValueError: abort(400,description='Página inválida.')
        clause=' AND '.join(where)
        total=db().execute('SELECT count(*) FROM calificacion c WHERE '+clause,params).fetchone()[0]
        items=[dict(r) for r in db().execute('SELECT c.*,b.codigo corredor FROM calificacion c JOIN corredor b ON b.id=c.corredor_id WHERE '+clause+' ORDER BY c.id DESC LIMIT 50 OFFSET ?',params+[(page-1)*50])]
        return jsonify(items=items,total=total,page=page,pages=max(1,(total+49)//50))

    @app.get('/api/ratings/<int:rid>')
    @need_user(('operador','supervisor'))
    def detail(rid): return jsonify(item=rating_object(rid))

    def catalog_entry(conn,data):
        return conn.execute('SELECT * FROM instrumento WHERE mercado=? AND codigo=?',(data['mercado'],data['instrumento'])).fetchone()

    def catalog_problem(entry,data):
        """DEMO-2: un instrumento inscrito debe existir en el catálogo del mercado y estar habilitado.

        Un no inscrito que no figura en el catálogo es admisible; si figura, debe coincidir y estar habilitado.
        La previsualización usa esta función; las escrituras repiten la condición en la misma sentencia
        (CATALOG_GUARD). Un cambio del catálogo rige para las operaciones posteriores y no altera los
        registros ya guardados.
        """
        if entry is None:
            return 'Instrumento: un instrumento inscrito debe existir en el catálogo del mercado (regla DEMO-2).' if data['inscrito'] else None
        if not entry['habilitado']: return 'Instrumento: está deshabilitado en el catálogo (regla DEMO-2).'
        if entry['inscrito']!=data['inscrito']:
            return 'Inscripción: el catálogo registra el instrumento como '+('inscrito' if entry['inscrito'] else 'no inscrito')+' (regla DEMO-2).'
        return None

    def check_catalog(conn,data):
        problem=catalog_problem(catalog_entry(conn,data),data)
        if problem: raise ValidationError(problem)

    def existing_record(conn,broker,row):
        return conn.execute('SELECT id,origen,version FROM calificacion WHERE corredor_id=? AND mercado=? AND periodo=? AND instrumento=? AND calificacion=? AND activo=1',(broker,*business_key(row))).fetchone()

    def explain_write_conflict(broker,data):
        """Explica un rechazo del índice único: la consulta solo se hace después del rechazo, no en cada guardado."""
        current=existing_record(db(),broker,data)
        if current and current['origen']==BOLSA: abort(409,description=BOLSA_PRIORITY_MESSAGE)

    def require_bolsa_permission(record):
        """DEMO-3: un registro informado por Bolsa solo lo modifica o desactiva el supervisor."""
        if record['origen']==BOLSA and g.user['rol']!='supervisor':
            security('prioridad_bolsa_denegada')
            abort(403,description='Registro informado por Bolsa: solo el supervisor puede modificarlo o desactivarlo (regla DEMO-3).')

    def replace_with_bolsa(conn,current,clean,broker):
        """DEMO-3: reemplaza los valores del corredor; los anteriores quedan en la bitácora."""
        before=dict(conn.execute('SELECT * FROM calificacion WHERE id=?',(current['id'],)).fetchone())
        fields=dict(**clean,origen=BOLSA,actualizado=stamp())
        cur=conn.execute('UPDATE calificacion SET '+','.join(k+'=?' for k in fields)+',version=version+1 WHERE id=? AND version=? AND activo=1 AND '+CATALOG_GUARD,
                         tuple(fields.values())+(current['id'],current['version'])+catalog_guard_params(clean))
        if cur.rowcount!=1: abort(409,description='Un registro cambió después de la previsualización. La carga no se guardó; volver a validar.')
        after=dict(conn.execute('SELECT * FROM calificacion WHERE id=?',(current['id'],)).fetchone())
        event(conn,'prioridad_bolsa','calificacion',current['id'],broker,before,after)
        return current['id']

    def insert_rating(conn,data,broker,origin):
        now=stamp()
        fields=dict(corredor_id=broker,**data,origen=origin,creado=now,actualizado=now)
        cur=conn.execute('INSERT INTO calificacion ('+','.join(fields)+') SELECT '+','.join('?'*len(fields))+' WHERE '+CATALOG_GUARD,
                         tuple(fields.values())+catalog_guard_params(data))
        if cur.rowcount!=1: raise CatalogConflict()
        after=dict(conn.execute('SELECT * FROM calificacion WHERE id=?',(cur.lastrowid,)).fetchone())
        event(conn,'crear','calificacion',cur.lastrowid,broker,after=after)
        return cur.lastrowid

    @app.post('/api/ratings')
    @need_user(('operador','supervisor'))
    def create_rating():
        payload=json_payload(); broker=require_broker(payload.get('broker'))
        require_factor_permission(payload.get('mode'))
        data=validate_rating(payload)
        try:
            with db(): rid=insert_rating(db(),data,broker,'manual')
        except CatalogConflict:
            check_catalog(db(),data); abort(409,description=CATALOG_WRITE_MESSAGE)
        except sqlite3.IntegrityError:
            explain_write_conflict(broker,data); raise
        return jsonify(ok=True,id=rid),201

    @app.post('/api/factor/preview')
    @need_user(('operador','supervisor'))
    def preview_factor():
        payload=json_payload()
        return jsonify(factor=factor_demo(payload.get('amount'),payload.get('base')),rule='DEMO-1',approved=False)

    @app.put('/api/ratings/<int:rid>')
    @need_user(('operador','supervisor'))
    def update_rating(rid):
        before=rating_object(rid); require_bolsa_permission(before)
        payload=json_payload(); require_factor_permission(payload.get('mode'))
        data=validate_rating(payload)
        if not before['activo']: abort(409,description='El registro está inactivo.')
        try: version=int(payload.get('version',0))
        except (ValueError,TypeError): version=0
        try:
            with db():
                fields=dict(**data,actualizado=stamp())
                cur=db().execute('UPDATE calificacion SET '+','.join(k+'=?' for k in fields)+',version=version+1 WHERE id=? AND version=? AND activo=1 AND '+CATALOG_GUARD,
                                 tuple(fields.values())+(rid,version)+catalog_guard_params(data))
                if cur.rowcount!=1:
                    check_catalog(db(),data)   # 422 si el motivo es el catálogo; si no, fue otra versión del registro
                    abort(409,description='Otro usuario cambió el registro. Recargar antes de editar.')
                after=dict(db().execute('SELECT * FROM calificacion WHERE id=?',(rid,)).fetchone())
                event(db(),'modificar','calificacion',rid,before['corredor_id'],before,after)
        except sqlite3.IntegrityError:
            explain_write_conflict(before['corredor_id'],data); raise
        return jsonify(ok=True)

    @app.delete('/api/ratings/<int:rid>')
    @need_user(('operador','supervisor'))
    def delete_rating(rid):
        before=rating_object(rid); require_bolsa_permission(before); payload=json_payload()
        try: version=int(payload.get('version',0))
        except (ValueError,TypeError): version=0
        with db():
            cur=db().execute('UPDATE calificacion SET activo=0,version=version+1,actualizado=? WHERE id=? AND activo=1 AND version=?',(stamp(),rid,version))
            if cur.rowcount!=1: abort(409,description='El registro cambió o ya está inactivo. Recargar la consulta.')
            after=dict(db().execute('SELECT * FROM calificacion WHERE id=?',(rid,)).fetchone())
            event(db(),'inactivar','calificacion',rid,before['corredor_id'],before,after)
        return jsonify(ok=True)

    def file_record(conn,batch,content,original,kind,ext,created_paths):
        internal=secrets.token_hex(24)+ext
        path=Path(app.config['PRIVATE'])/internal
        # Register ownership before writing: a failure during or immediately
        # after file creation must not leave an untracked private artifact.
        created_paths.append(path)
        path.write_bytes(content)
        conn.execute('INSERT INTO archivo (carga_id,clase,nombre_original,nombre_interno,tipo,bytes,sha256,creado) VALUES (?,?,?,?,?,?,?,?)',
                     (batch,kind,original[:120],internal,'text/csv' if ext=='.csv' else 'application/json',len(content),hashlib.sha256(content).hexdigest(),stamp()))
        return path

    @app.post('/api/batches/preview')
    @need_user(('operador','supervisor'))
    def preview():
        broker=require_broker(request.form.get('broker'))
        kind=request.form.get('kind')
        if kind not in BATCH_KINDS: raise ValidationError('Tipo de carga inválido.')
        if kind==BOLSA:
            # DEMO-3: el archivo de Bolsa no es ingreso manual del corredor; lo carga solo el supervisor.
            if g.user['rol']!='supervisor':
                security('carga_bolsa_denegada')
                abort(403,description='Solo el supervisor puede cargar archivos informados por Bolsa (regla DEMO-3).')
        else: require_factor_permission('factor' if kind=='factores-DEMO' else 'monto')
        upload=request.files.get('file')
        if not upload or not upload.filename.lower().endswith('.csv'): raise ValidationError('Solo se admiten archivos .csv académicos.')
        if upload.mimetype not in ('text/csv','application/vnd.ms-excel','text/plain','application/octet-stream'): raise ValidationError('Tipo de archivo no permitido.')
        content=upload.read(MAX_FILE_BYTES+1); raw_rows=parse_csv(content); processed=[]; seen=set()
        for number,raw in raw_rows:
            errors=[]; clean=None; notice=None
            try:
                clean=validate_rating(raw)
                if kind=='DJ1948-DEMO' and raw['mode']!='monto': raise ValidationError('DJ1948-DEMO requiere mode=monto.')
                if kind in ('factores-DEMO',BOLSA) and raw['mode']!='factor': raise ValidationError(kind+' requiere mode=factor.')
                key=business_key(clean)
                if key in seen: raise ValidationError('Duplicado dentro del archivo según llave provisional.')
                check_catalog(db(),clean)
                current=existing_record(db(),broker,clean)
                if current and current['origen']==BOLSA:
                    raise ValidationError('Duplicado: ya existe un registro informado por Bolsa con la misma llave provisional (regla DEMO-3).' if kind==BOLSA else BOLSA_PRIORITY_MESSAGE)
                if current and kind!=BOLSA: raise ValidationError('Duplicado ya registrado según llave provisional.')
                if current: notice=f'Reemplazará el registro {current["id"]} (origen {current["origen"]}) por prioridad Bolsa (regla DEMO-3).'
                seen.add(key)
            except ValidationError as error: errors.append(str(error))
            processed.append(dict(number=number,raw=raw,clean=clean,errors=errors,notice=notice))
        invalid=sum(bool(r['errors']) for r in processed); replacements=sum(bool(r['notice']) and not r['errors'] for r in processed)
        created_paths=[]; batch=None
        try:
            with db():
                cur=db().execute('INSERT INTO carga (corredor_id,usuario_id,tipo,estado,total,validas,invalidas,creado,token) VALUES (?,?,?,?,?,?,?,?,?)',
                    (broker,g.user['id'],kind,'rechazada' if invalid else 'lista',len(processed),len(processed)-invalid,invalid,stamp(),secrets.token_urlsafe(24)))
                batch=cur.lastrowid
                for row in processed:
                    db().execute('INSERT INTO carga_fila (carga_id,numero,datos_json,errores_json) VALUES (?,?,?,?)',
                        (batch,row['number'],canonical(row['raw']),canonical(row['errors'])))
                file_record(db(),batch,content,upload.filename,'original','.csv',created_paths)
                report=dict(demo=True,policy='Rechazo total si alguna fila tiene errores',batch=batch,rows=processed,total=len(processed),invalid=invalid,
                            rules=[CATALOG_RULE]+([BOLSA_RULE] if kind==BOLSA else []),replacements=replacements)
                file_record(db(),batch,canonical(report).encode(),f'reporte-{batch}.json','reporte','.json',created_paths)
                batch_data=dict(db().execute('SELECT * FROM carga WHERE id=?',(batch,)).fetchone())
                documentrepo.upsert_report(app.config['PRIVATE'],batch_data,report,hashlib.sha256(canonical(report).encode()).hexdigest())
                event(db(),'prevalidar','carga',batch,broker,after=dict(total=len(processed),invalidas=invalid,tipo=kind,reemplazos=replacements))
        except Exception:
            if batch is not None:
                try: documentrepo.remove_report(app.config['PRIVATE'],batch)
                except documentrepo.DocumentStoreError: pass
            for path in created_paths:
                if path.exists(): path.unlink()
            raise
        return jsonify(id=batch,document_id=batch,total=len(processed),valid=len(processed)-invalid,invalid=invalid,replacements=replacements,rows=processed,can_confirm=not invalid)

    def batch_object(bid):
        row=db().execute('SELECT * FROM carga WHERE id=?',(bid,)).fetchone()
        if not row or row['corredor_id'] not in allowed_brokers():
            security('carga_no_disponible')
            abort(404,description='Carga no disponible.')
        return dict(row)

    @app.post('/api/batches/<int:bid>/confirm')
    @need_user(('operador','supervisor'))
    def confirm_batch(bid):
        batch=batch_object(bid)
        if batch['estado']=='confirmada':
            documentrepo.update_state(app.config['PRIVATE'],bid,'confirmada')
            return jsonify(ok=True,idempotent=True,inserted=batch['validas'])
        if batch['estado']!='lista': abort(409,description='La carga contiene errores o está en conflicto. Corregir y subir otro archivo.')
        rows=db().execute('SELECT * FROM carga_fila WHERE carga_id=? ORDER BY numero',(bid,)).fetchall()
        with db():
            db().execute('BEGIN IMMEDIATE')
            state=db().execute('SELECT estado FROM carga WHERE id=?',(bid,)).fetchone()[0]
            if state=='confirmada': return jsonify(ok=True,idempotent=True,inserted=batch['validas'])
            replaced=0
            # El catálogo se relee una vez dentro de la transacción: un cambio posterior a la previsualización revierte la carga.
            catalog={(entry['mercado'],entry['codigo']):entry for entry in db().execute('SELECT mercado,codigo,inscrito,habilitado FROM instrumento')}
            for row in rows:
                clean=validate_rating(json.loads(row['datos_json']))
                if catalog_problem(catalog.get((clean['mercado'],clean['instrumento'])),clean): abort(409,description=CATALOG_CHANGED_MESSAGE)
                current=existing_record(db(),batch['corredor_id'],clean)
                if current and (batch['tipo']!=BOLSA or current['origen']==BOLSA):
                    abort(409,description='Un registro apareció después de la previsualización. La carga no se guardó; volver a validar.')
                if current:
                    rid=replace_with_bolsa(db(),current,clean,batch['corredor_id']); replaced+=1
                else: rid=insert_rating(db(),clean,batch['corredor_id'],batch['tipo'])
                db().execute('UPDATE carga_fila SET calificacion_id=? WHERE id=?',(rid,row['id']))
            db().execute("UPDATE carga SET estado='confirmada',confirmado=? WHERE id=?",(stamp(),bid))
            event(db(),'confirmar','carga',bid,batch['corredor_id'],before=dict(estado='lista'),after=dict(estado='confirmada',insertadas=len(rows),reemplazadas=replaced))
        documentrepo.update_state(app.config['PRIVATE'],bid,'confirmada')
        return jsonify(ok=True,inserted=len(rows),replaced=replaced,idempotent=False)

    @app.get('/api/documents')
    @need_user(('operador','supervisor'))
    def documents():
        items=documentrepo.reports_for_brokers(app.config['PRIVATE'],allowed_brokers())
        verified=[]
        for item in items:
            if type(item.get('batch_id')) is not int: continue
            batch=db().execute('SELECT corredor_id,estado FROM carga WHERE id=?',(item['batch_id'],)).fetchone()
            if not batch or batch['corredor_id'] not in allowed_brokers() or batch['corredor_id']!=item.get('broker_id'): continue
            item['state']=batch['estado']
            verified.append({key:value for key,value in item.items() if key!='report'})
        return jsonify(engine='TinyDB 4.9.0',items=verified)

    @app.get('/api/documents/<int:bid>')
    @need_user(('operador','supervisor'))
    def document_detail(bid):
        batch=batch_object(bid)
        document=documentrepo.report_by_batch(app.config['PRIVATE'],bid)
        if document is None or document.get('broker_id')!=batch['corredor_id']:
            abort(404,description='Documento no disponible.')
        metadata=db().execute("SELECT sha256 FROM archivo WHERE carga_id=? AND clase='reporte' ORDER BY id DESC LIMIT 1",(bid,)).fetchone()
        if not metadata or document.get('source_sha256')!=metadata['sha256'] or hashlib.sha256(canonical(document.get('report')).encode()).hexdigest()!=metadata['sha256']:
            security('integridad_documento_fallida')
            abort(409,description='El documento no supera la verificación de integridad.')
        # State comes from SQLite, so a delayed derived-store update cannot alter truth.
        document['state']=batch['estado']
        return jsonify(engine='TinyDB 4.9.0',document=document)

    @app.get('/api/batches')
    @need_user(('operador','supervisor'))
    def batches():
        ids=allowed_brokers()
        if not ids: return jsonify(items=[])
        items=[dict(r) for r in db().execute('SELECT * FROM carga WHERE corredor_id IN ('+','.join('?'*len(ids))+') ORDER BY id DESC LIMIT 30',ids)]
        for row in items: row['files']=[dict(f) for f in db().execute('SELECT id,clase,nombre_original,sha256,bytes FROM archivo WHERE carga_id=?',(row['id'],))]
        return jsonify(items=items)

    @app.get('/api/files/<int:fid>')
    @need_user(('operador','supervisor'))
    def download(fid):
        row=db().execute('SELECT * FROM archivo WHERE id=?',(fid,)).fetchone()
        if not row: abort(404,description='Archivo no disponible.')
        batch_object(row['carga_id'])
        path=Path(app.config['PRIVATE'])/row['nombre_interno']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:
            security('integridad_archivo_fallida'); abort(409,description='El archivo no supera la verificación de integridad.')
        with db(): event(db(),'descargar','archivo',fid,db().execute('SELECT corredor_id FROM carga WHERE id=?',(row['carga_id'],)).fetchone()[0])
        return send_file(path,mimetype=row['tipo'],as_attachment=True,download_name='reporte-demo.json' if row['clase']=='reporte' else 'original-demo.csv')

    @app.get('/api/audit')
    @need_user()
    def audit():
        if g.user['rol']=='administrador': where='corredor_id IS NULL'; params=[]
        elif g.user['rol']=='operador':
            ids=allowed_brokers()
            where='usuario_id=? AND corredor_id IN ('+','.join('?'*len(ids))+')' if ids else '0=1'
            params=[g.user['id'],*ids] if ids else []
        else:
            # El catálogo es común a los corredores: sus cambios quedan sin corredor y los revisa el supervisor.
            ids=allowed_brokers()
            where=('corredor_id IN ('+','.join('?'*len(ids))+') OR ' if ids else '')+"(entidad='instrumento' AND corredor_id IS NULL)"; params=ids
        items=[dict(r) for r in db().execute('SELECT * FROM evento_auditoria WHERE '+where+' ORDER BY id DESC LIMIT 100',params)]
        previous='0'*64; integrity=True
        for row in db().execute('SELECT * FROM evento_auditoria ORDER BY id'):
            values=dict(row); values.pop('id'); digest=values.pop('hash_evento')
            if values['hash_anterior']!=previous or not hmac.compare_digest(digest,hmac.new(app.secret_key,canonical(values).encode(),hashlib.sha256).hexdigest()): integrity=False
            previous=digest
        return jsonify(items=items,integrity=integrity)

    @app.get('/api/users')
    @need_user(('administrador',))
    def users():
        items=[dict(r) for r in db().execute('SELECT u.id,u.nombre,u.login,u.activo,u.version,r.nombre rol FROM usuario u JOIN rol r ON u.rol_id=r.id ORDER BY u.id')]
        for item in items: item['brokers']=[r[0] for r in db().execute('SELECT corredor_id FROM usuario_corredor WHERE usuario_id=?',(item['id'],))]
        return jsonify(items=items,brokers=[dict(r) for r in db().execute('SELECT * FROM corredor')])

    @app.put('/api/users/<int:uid>')
    @need_user(('administrador',))
    def update_user(uid):
        if uid==g.user['id']: abort(409,description='No se permite modificar el propio perfil administrador en esta demostración.')
        payload=json_payload(); role=payload.get('role'); brokers=payload.get('brokers',[])
        if role not in ('operador','supervisor','administrador') or not isinstance(brokers,list) or len(brokers)>10: raise ValidationError('Perfil o corredores inválidos.')
        if role=='administrador' and brokers: raise ValidationError('El administrador no recibe acceso tributario por defecto.')
        before=db().execute('SELECT id,nombre,login,rol_id,activo,version FROM usuario WHERE id=?',(uid,)).fetchone()
        if not before: abort(404,description='Usuario no disponible.')
        valid_ids={r[0] for r in db().execute('SELECT id FROM corredor')}
        if any(type(b) is not int or b not in valid_ids for b in brokers): raise ValidationError('Corredor inválido.')
        active=payload.get('active')
        if type(active) is not bool: raise ValidationError('Estado de usuario inválido.')
        try: version=int(payload.get('version',0))
        except (ValueError,TypeError): version=0
        with db():
            role_id=db().execute('SELECT id FROM rol WHERE nombre=?',(role,)).fetchone()[0]
            cur=db().execute('UPDATE usuario SET rol_id=?,activo=?,version=version+1 WHERE id=? AND version=?',(role_id,int(active),uid,version))
            if cur.rowcount!=1: abort(409,description='El usuario cambió; recargar la lista.')
            db().execute('DELETE FROM usuario_corredor WHERE usuario_id=?',(uid,))
            for broker in sorted(set(brokers)): db().execute('INSERT INTO usuario_corredor VALUES (?,?)',(uid,broker))
            after=dict(db().execute('SELECT id,nombre,login,rol_id,activo,version FROM usuario WHERE id=?',(uid,)).fetchone()); after['brokers']=brokers
            event(db(),'cambiar_perfil','usuario',uid,before=dict(before),after=after)
        return jsonify(ok=True)

    @app.get('/api/instruments')
    @need_user(('operador','supervisor'))
    def instruments():
        where=['1=1']; params=[]
        if request.args.get('market'): where.append('mercado=?'); params.append(request.args['market'][:3].upper())
        if request.args.get('q'): where.append('codigo LIKE ?'); params.append('%'+request.args['q'][:40].upper()+'%')
        clause=' AND '.join(where)
        total=db().execute('SELECT count(*) FROM instrumento WHERE '+clause,params).fetchone()[0]
        items=[dict(r) for r in db().execute('SELECT * FROM instrumento WHERE '+clause+' ORDER BY mercado,codigo LIMIT 200',params)]
        return jsonify(items=items,total=total,rule=CATALOG_RULE,approved=False)

    @app.post('/api/instruments')
    @need_user(('supervisor',))
    def add_instrument():
        payload=json_payload()
        market=str(payload.get('market','')).strip().upper(); code=str(payload.get('code','')).strip().upper()
        if market not in ('SCL','COL','LIM'): raise ValidationError('Mercado: seleccionar SCL, COL o LIM.')
        if not re.fullmatch(r'[A-Z0-9][A-Z0-9._-]{0,39}',code): raise ValidationError('Código: usar 1 a 40 letras, números, punto, guion o guion bajo.')
        if str(payload.get('registered','')) not in ('0','1'): raise ValidationError('Inscripción: seleccionar 1 (inscrito) o 0 (no inscrito).')
        now=stamp()
        with db():
            cur=db().execute('INSERT INTO instrumento (mercado,codigo,inscrito,habilitado,creado,actualizado) VALUES (?,?,?,1,?,?)',(market,code,int(payload['registered']),now,now))
            after=dict(db().execute('SELECT * FROM instrumento WHERE id=?',(cur.lastrowid,)).fetchone())
            event(db(),'agregar_instrumento','instrumento',cur.lastrowid,after=after)
        return jsonify(ok=True,id=cur.lastrowid),201

    @app.put('/api/instruments/<int:iid>')
    @need_user(('supervisor',))
    def update_instrument(iid):
        payload=json_payload(); enabled=payload.get('enabled')
        if type(enabled) is not bool: raise ValidationError('Estado del instrumento inválido.')
        try: version=int(payload.get('version',0))
        except (ValueError,TypeError): version=0
        before=db().execute('SELECT * FROM instrumento WHERE id=?',(iid,)).fetchone()
        if not before: abort(404,description='Instrumento no disponible.')
        with db():
            cur=db().execute('UPDATE instrumento SET habilitado=?,version=version+1,actualizado=? WHERE id=? AND version=?',(int(enabled),stamp(),iid,version))
            if cur.rowcount!=1: abort(409,description='El instrumento cambió; recargar el catálogo.')
            after=dict(db().execute('SELECT * FROM instrumento WHERE id=?',(iid,)).fetchone())
            event(db(),'habilitar_instrumento' if enabled else 'deshabilitar_instrumento','instrumento',iid,before=dict(before),after=after)
        return jsonify(ok=True)

    @app.get('/api/template/<kind>')
    @need_user(('operador','supervisor'))
    def template(kind):
        if kind not in ('montos','factores','bolsa'): abort(404)
        if kind=='bolsa' and g.user['rol']!='supervisor':
            security('permiso_denegado'); abort(403,description='El perfil no tiene permiso para esta operación.')
        buffer=io.StringIO(); writer=csv.writer(buffer,lineterminator='\n'); writer.writerow(CSV_COLUMNS)
        if kind=='bolsa': writer.writerow(['SCL','2026-10','DEMO-ALFA','Tributaria demo','factor','','','0.300000','1'])
        else: writer.writerow(['SCL','2026-10','DEMO-ARCHIVO','Tributaria demo','monto' if kind=='montos' else 'factor','250' if kind=='montos' else '', '1000' if kind=='montos' else '', '' if kind=='montos' else '0.25','0'])
        return send_file(io.BytesIO(buffer.getvalue().encode()),mimetype='text/csv',as_attachment=True,download_name=f'plantilla-{kind}-DEMO.csv')

    with app.app_context():
        conn=db()
        # WAL: las consultas no bloquean al escritor ni este a las consultas (hallazgo de la prueba de estrés).
        # Es persistente en el archivo; synchronous queda en FULL para no perder transacciones confirmadas.
        conn.execute('PRAGMA journal_mode=WAL')
        conn.executescript((ROOT/'schema.sql').read_text(encoding='utf-8'))
        app.config['DUMMY_HASH']=generate_password_hash(secrets.token_urlsafe(24),method='pbkdf2:sha256:600000')
        if not conn.execute('SELECT count(*) FROM usuario').fetchone()[0]:
            with conn:
                conn.executemany('INSERT INTO rol (id,nombre) VALUES (?,?)',[(1,'operador'),(2,'supervisor'),(3,'administrador')])
                conn.executemany('INSERT INTO corredor (id,codigo,nombre) VALUES (?,?,?)',[(1,'DEMO-A','Corredor ficticio A'),(2,'DEMO-B','Corredor ficticio B')])
                for uid,name,login,rid in [(1,'Operador ficticio A','operador_a',1),(2,'Operador ficticio B','operador_b',1),(3,'Supervisor ficticio','supervisor',2),(4,'Administrador ficticio','admin',3)]:
                    conn.execute('INSERT INTO usuario (id,nombre,login,password_hash,rol_id) VALUES (?,?,?,?,?)',(uid,name,login,generate_password_hash(DEMO_PASSWORD,method='pbkdf2:sha256:600000'),rid))
                conn.executemany('INSERT INTO usuario_corredor VALUES (?,?)',[(1,1),(2,2),(3,1),(3,2)])
                conn.execute('INSERT INTO regla_factor VALUES (1,?,?,?,0)',('DEMO-1','Regla exclusivamente ilustrativa: monto/base; HALF_UP; 6 decimales',canonical(dict(precision=6,rounding='HALF_UP',min=0,max=1))))
                now=stamp()
                conn.executemany('INSERT INTO instrumento (mercado,codigo,inscrito,habilitado,creado,actualizado) VALUES (?,?,?,?,?,?)',
                                 [(market,code,registered,enabled,now,now) for market,code,registered,enabled in CATALOG_SEED])
                for broker,inst,amount in [(1,'DEMO-ALFA','250'),(1,'DEMO-NO-INSCRITO','120'),(2,'DEMO-BETA','400')]:
                    clean=validate_rating(dict(market='SCL',period='2026-10',instrument=inst,rating='Tributaria demo',mode='monto',amount=amount,base='1000',registered='0' if 'NO-' in inst else '1'))
                    insert_rating(conn,clean,broker,'manual')
        # Upgrade the user's earlier fictitious demo reports without overwriting SQL.
        for row in conn.execute("SELECT a.*,c.corredor_id,c.usuario_id,c.tipo carga_tipo,c.estado,c.creado carga_creado FROM archivo a JOIN carga c ON c.id=a.carga_id WHERE a.clase='reporte'").fetchall():
            try:
                if documentrepo.report_by_batch(app.config['PRIVATE'],row['carga_id']) is not None: continue
            except documentrepo.DocumentStoreError:
                app.logger.error('Repositorio documental no disponible; SQLite permanece operativo.')
                break
            path=Path(app.config['PRIVATE'])/row['nombre_interno']
            if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']:
                documentrepo.upsert_report(app.config['PRIVATE'],dict(id=row['carga_id'],corredor_id=row['corredor_id'],usuario_id=row['usuario_id'],tipo=row['carga_tipo'],estado=row['estado'],creado=row['carga_creado']),json.loads(path.read_text(encoding='utf-8')),row['sha256'])
    app.db=db; app.event=event
    return app

if __name__=='__main__':
    application=create_app()
    # Only loopback; no debug/reloader or production claims.
    application.run(host='127.0.0.1',port=8765,debug=False,use_reloader=False,threaded=True)
