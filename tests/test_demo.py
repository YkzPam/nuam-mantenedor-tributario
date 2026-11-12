"""Pruebas reales y aisladas: no modifican la base de la demostración visible."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'vendor'))
import io
import json
import shutil
import sqlite3
import tempfile
import time
import tracemalloc
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from decimal import Decimal
import app as demo
from domain import ValidationError, factor_demo, validate_rating, parse_csv, CSV_COLUMNS, business_key

METRICS={}
VALID=dict(broker=1,market='SCL',period='2026-10',instrument='TEST-NEW',rating='Tributaria demo',registered='0',mode='monto',amount='250',base='1000')

class UnitCases(unittest.TestCase):
    def test_U01_decimal_conversion(self):
        """U01 | unitario | conversión Decimal exacta y HALF_UP"""
        self.assertEqual(factor_demo('1','3'),'0.333333'); self.assertEqual(factor_demo('1','2000000'),'0.000001')
        self.assertEqual(factor_demo(0,1000),'0.000000')
    def test_U02_zero_base(self):
        """U02 | unitario | impedir división por cero"""
        with self.assertRaises(ValidationError): factor_demo('0','0')
    def test_U03_negative_nonfinite_limit(self):
        """U03 | unitario | rechazar negativos, NaN, infinito y exceso de precisión"""
        for value in ['-1','NaN','Infinity','1.0000001','1000000000001']:
            with self.subTest(value=value),self.assertRaises(ValidationError): factor_demo(value,'1000')
    def test_U04_factor_range(self):
        """U04 | unitario | factor directo fuera de rango y monto mayor que base"""
        with self.assertRaises(ValidationError): factor_demo('2','1')
        with self.assertRaises(ValidationError): validate_rating(dict(VALID,mode='factor',factor='1.01'))
        self.assertEqual(validate_rating(dict(VALID,mode='factor',factor='0'))['factor'],'0.000000')
    def test_U05_required_period_instrument(self):
        """U05 | unitario | obligatorios, mes inválido y caracteres no permitidos"""
        for payload in [dict(VALID,rating=''),dict(VALID,period='2026-13'),dict(VALID,instrument='<script>'),dict(VALID,market='OTRO')]:
            with self.subTest(payload=payload),self.assertRaises(ValidationError): validate_rating(payload)
    def test_U06_provisional_key(self):
        """U06 | unitario | llave provisional compuesta y normalización de instrumento"""
        row=validate_rating(dict(VALID,instrument='demo-x'))
        self.assertEqual(business_key(row),('SCL','2026-10','DEMO-X','Tributaria demo'))
    def test_U07_csv_header(self):
        """U07 | unitario | encabezado exacto CSV"""
        with self.assertRaises(ValidationError): parse_csv(b'a,b\n1,2')
    def test_U08_csv_binary_encoding(self):
        """U08 | unitario | contenido binario, UTF-8 incorrecto y tamaño excesivo"""
        for content in [b'\x00',b'\xff\xfe',b'x'*500001,b'']:
            with self.subTest(size=len(content)),self.assertRaises(ValidationError): parse_csv(content)
    def test_U09_csv_limit_columns(self):
        """U09 | unitario | máximo de filas y cantidad de columnas"""
        header=','.join(CSV_COLUMNS)+'\n'
        with self.assertRaises(ValidationError): parse_csv((header+'a,b\n').encode())
        row='SCL,2026-10,A,Demo,factor,,,0.1,1\n'
        with self.assertRaises(ValidationError): parse_csv((header+row*1001).encode())
    def test_U10_non_registered(self):
        """U10 | unitario | instrumentos no inscritos"""
        self.assertEqual(validate_rating(VALID)['inscrito'],0)

class IntegrationCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace=tempfile.TemporaryDirectory(prefix='nuam-tests-')
        cls.root=Path(cls.workspace.name); cls.application=demo.create_app(cls.root/'seed',testing=True)
    @classmethod
    def tearDownClass(cls): cls.workspace.cleanup()
    def setUp(self):
        self.case_dir=Path(tempfile.mkdtemp(prefix='case-',dir=self.root)); (self.case_dir/'private').mkdir()
        shutil.copy2(self.root/'seed'/'demo.sqlite3',self.case_dir/'case.sqlite3')
        self.application.config['DATABASE']=str(self.case_dir/'case.sqlite3');self.application.config['PRIVATE']=str(self.case_dir/'private')
        demo.RATE_FAILURES.clear();self.client=self.application.test_client();self.login(self.client)
    def token(self,client=None): return (client or self.client).get('/api/me').json['csrf']
    def login(self,client,login='operador_a'):
        response=client.post('/api/login',json=dict(login=login,password=demo.DEMO_PASSWORD),headers={'X-CSRF-Token':self.token(client)})
        self.assertEqual(response.status_code,200)
    def request(self,path,method='post',payload=None,client=None):
        client=client or self.client
        return getattr(client,method)(path,json=payload if payload is not None else {},headers={'X-CSRF-Token':self.token(client)})
    def sql(self,sql,params=()):
        with sqlite3.connect(self.application.config['DATABASE']) as conn:
            conn.execute('PRAGMA foreign_keys=ON'); return conn.execute(sql,params).fetchall()
    def create(self,**changes):
        response=self.request('/api/ratings',payload=dict(VALID,**changes));self.assertEqual(response.status_code,201);return response.json['id']
    def csv(self,rows): return (','.join(CSV_COLUMNS)+'\n'+'\n'.join(rows)+'\n').encode()
    def preview(self,content,kind='DJ1948-DEMO',filename='demo.csv',client=None,broker='1'):
        client=client or self.client
        return client.post('/api/batches/preview',data={'broker':broker,'kind':kind,'file':(io.BytesIO(content),filename)},headers={'X-CSRF-Token':self.token(client)})
    def test_I01_create_query_details(self):
        """I01 | integración | crear y consultar por mercado/período/texto"""
        rid=self.create();result=self.client.get('/api/ratings?q=TEST-NEW&market=SCL&period=2026-10')
        self.assertEqual(result.json['total'],1);self.assertEqual(self.client.get(f'/api/ratings/{rid}').json['item']['factor'],'0.250000')
    def test_I02_update_audit(self):
        """I02 | integración | modificar con auditoría transaccional antes/después"""
        rid=self.create();self.assertEqual(self.request(f'/api/ratings/{rid}','put',dict(VALID,amount='500',version=1)).status_code,200)
        records=self.sql("SELECT antes_json,despues_json FROM evento_auditoria WHERE accion='modificar' AND registro_id=?",(rid,))
        self.assertEqual(json.loads(records[0][0])['factor'],'0.250000');self.assertEqual(json.loads(records[0][1])['factor'],'0.500000')
    def test_I03_inactivate(self):
        """I03 | integración | baja lógica conserva registro y bitácora"""
        rid=self.create();self.assertEqual(self.request(f'/api/ratings/{rid}','delete',dict(version=1)).status_code,200)
        self.assertEqual(self.client.get('/api/ratings?q=TEST-NEW').json['total'],0);self.assertEqual(self.sql('SELECT activo FROM calificacion WHERE id=?',(rid,))[0][0],0)
    def test_I04_duplicate_no_partial_audit(self):
        """I04 | integración | índice único rechaza duplicado sin cambio parcial"""
        self.create();before=len(self.sql('SELECT id FROM evento_auditoria'))
        self.assertEqual(self.request('/api/ratings',payload=VALID).status_code,409);self.assertEqual(len(self.sql('SELECT id FROM evento_auditoria')),before)
    def test_I05_concurrency(self):
        """I05 | integración | versión optimista evita sobrescritura de edición obsoleta"""
        rid=self.create();self.assertEqual(self.request(f'/api/ratings/{rid}','put',dict(VALID,version=1,amount='300')).status_code,200)
        self.assertEqual(self.request(f'/api/ratings/{rid}','put',dict(VALID,version=1,amount='900')).status_code,409)
        self.assertEqual(self.client.get(f'/api/ratings/{rid}').json['item']['monto'],'300')
    def test_I06_valid_bulk_idempotent(self):
        """I06 | integración | carga válida, confirmación y reintento idempotente"""
        result=self.preview(self.csv(['SCL,2026-10,BULK-A,Demo,monto,250,1000,,0']));self.assertEqual(result.status_code,200)
        bid=result.json['id'];confirmed=self.request(f'/api/batches/{bid}/confirm')
        self.assertEqual(confirmed.status_code,200);self.assertEqual(confirmed.json['inserted'],1);self.assertFalse(confirmed.json['idempotent'])
        self.assertEqual(self.sql('SELECT estado FROM carga WHERE id=?',(bid,)),[('confirmada',)])
        retry=self.request(f'/api/batches/{bid}/confirm')
        self.assertEqual(retry.status_code,200);self.assertEqual(retry.json['inserted'],1);self.assertTrue(retry.json['idempotent'])
        self.assertEqual(self.client.get('/api/ratings?q=BULK-A').json['total'],1)
        self.assertEqual(self.sql("SELECT count(*) FROM evento_auditoria WHERE accion='confirmar' AND registro_id=?",(bid,))[0][0],1)
    def test_I07_invalid_bulk_atomic(self):
        """I07 | integración | lote con duplicado y período inválido no guarda ninguna fila"""
        row='SCL,2026-10,BULK-A,Demo,monto,250,1000,,0'
        result=self.preview(self.csv([row,row,'SCL,2026-99,BULK-B,Demo,monto,1,2,,1']))
        self.assertEqual(result.json['invalid'],2);self.assertFalse(result.json['can_confirm'])
        self.assertEqual(self.request(f"/api/batches/{result.json['id']}/confirm").status_code,409);self.assertEqual(self.client.get('/api/ratings?q=BULK-').json['total'],0)
    def test_I08_bulk_concurrent_conflict_rollback(self):
        """I08 | integración | duplicado posterior a preview revierte todo el lote"""
        rows=['SCL,2026-10,BULK-FIRST,Demo,monto,1,2,,1','SCL,2026-10,BULK-CONFLICT,Demo,monto,1,2,,1']
        bid=self.preview(self.csv(rows)).json['id'];self.create(instrument='BULK-CONFLICT',rating='Demo')
        self.assertEqual(self.request(f'/api/batches/{bid}/confirm').status_code,409)
        self.assertEqual(self.client.get('/api/ratings?q=BULK-FIRST').json['total'],0)
    def test_I09_factor_bulk(self):
        """I09 | integración | CSV de factores sin inventar montos"""
        bid=self.preview(self.csv(['LIM,2026-10,FACTOR-DEMO,Demo,factor,,,0.5,0']),kind='factores-DEMO').json['id']
        self.assertEqual(self.request(f'/api/batches/{bid}/confirm').status_code,200)
        row=self.client.get('/api/ratings?q=FACTOR-DEMO').json['items'][0];self.assertEqual(row['factor'],'0.500000');self.assertIsNone(row['monto'])
    def test_I10_private_persistence_hash_json(self):
        """I10 | integración | CSV y JSON privados persistidos con hash/metadatos y descarga autorizada"""
        bid=self.preview(self.csv(['SCL,2026-10,FILE-DEMO,Demo,monto,1,2,,1'])).json['id']
        files=self.client.get('/api/batches').json['items'][0]['files'];self.assertEqual(len(files),2)
        for file in files:
            response=self.client.get('/api/files/'+str(file['id']));self.assertEqual(response.status_code,200);self.assertEqual(response.headers['X-Content-Type-Options'],'nosniff')
            import hashlib;self.assertEqual(hashlib.sha256(response.data).hexdigest(),file['sha256'])
            if file['clase']=='reporte':self.assertEqual(json.loads(response.data)['batch'],bid)
    def test_I11_foreign_keys(self):
        """I11 | integración | SQLite rechaza referencia de corredor inexistente"""
        with self.assertRaises(sqlite3.IntegrityError):
            self.sql('INSERT INTO usuario_corredor VALUES (?,?)',(1,999))
        self.assertEqual(self.sql('PRAGMA foreign_key_check'),[])
    def test_I12_documental_persistence_query(self):
        """I12 | integración | motor TinyDB persiste reporte y consulta SQL/documento funcional"""
        bid=self.preview(self.csv(['SCL,2026-10,DOC-DEMO,Demo,monto,1,2,,1'])).json['id']
        response=self.client.get('/api/documents/'+str(bid));self.assertEqual(response.status_code,200)
        self.assertEqual(response.json['engine'],'TinyDB 4.9.0');self.assertEqual(response.json['document']['report']['rows'][0]['clean']['factor'],'0.500000')
        from tinydb import TinyDB,Query
        path=Path(self.application.config['PRIVATE'])/'reportes.tinydb.json';self.assertTrue(path.is_file())
        with TinyDB(path,encoding='utf-8') as store:self.assertIsNotNone(store.table('reportes').get(Query().batch_id==bid))
        self.assertEqual(self.client.get('/api/documents').json['items'][0]['batch_id'],bid)
        self.request(f'/api/batches/{bid}/confirm');self.assertEqual(self.client.get('/api/documents/'+str(bid)).json['document']['state'],'confirmada')
    def test_S15_documental_authorization(self):
        """S15 | seguridad | documento TinyDB exige corredor y perfil; repositorio no es público"""
        bid=self.preview(self.csv(['SCL,2026-10,DOC-DEMO,Demo,monto,1,2,,1'])).json['id']
        other=self.application.test_client();self.login(other,'operador_b')
        self.assertEqual(other.get('/api/documents/'+str(bid)).status_code,404);self.assertEqual(other.get('/api/documents').json['items'],[])
        admin=self.application.test_client();self.login(admin,'admin');self.assertEqual(admin.get('/api/documents').status_code,403)
        self.assertEqual(self.client.get('/data/private/reportes.tinydb.json').status_code,404)
    def test_S16_documental_hash_corruption(self):
        """S16 | seguridad | reporte modificado devuelve 409 y repositorio corrupto devuelve 503 controlado"""
        bid=self.preview(self.csv(['SCL,2026-10,DOC-DEMO,Demo,monto,1,2,,1'])).json['id']
        from tinydb import TinyDB,Query
        path=Path(self.application.config['PRIVATE'])/'reportes.tinydb.json'
        with TinyDB(path,encoding='utf-8') as store:store.table('reportes').update(dict(report={'fake':True}),Query().batch_id==bid)
        self.assertEqual(self.client.get('/api/documents/'+str(bid)).status_code,409)
        path.write_text('{not-json',encoding='utf-8')
        self.assertEqual(self.client.get('/api/documents').status_code,503);self.assertEqual(self.client.get('/api/ratings').status_code,200)
        path.write_text('{"reportes":true}',encoding='utf-8')
        self.assertEqual(self.client.get('/api/documents').status_code,503)
    def test_S01_unauthenticated(self):
        """S01 | seguridad | API no expone registros sin sesión"""
        client=self.application.test_client();self.assertEqual(client.get('/api/ratings').status_code,401)
    def test_S02_csrf_nomutation(self):
        """S02 | seguridad | token CSRF ausente/incorrecto impide escrituras"""
        before=len(self.sql('SELECT id FROM calificacion'))
        for token in ['', 'fake']:
            self.assertEqual(self.client.post('/api/ratings',json=VALID,headers={'X-CSRF-Token':token}).status_code,403)
        self.assertEqual(len(self.sql('SELECT id FROM calificacion')),before)
    def test_S03_broker_object_boundaries(self):
        """S03 | seguridad | corredor ajeno no se lista ni se accede mediante identificador"""
        self.assertEqual(self.client.get('/api/ratings').json['total'],2)
        for rid in [3,999999]:self.assertEqual(self.client.get('/api/ratings/'+str(rid)).status_code,404)
        self.assertEqual(self.request('/api/ratings',payload=dict(VALID,broker=2)).status_code,403)
        self.assertEqual(self.request('/api/ratings/3','put',dict(VALID,version=1)).status_code,404)
    def test_S04_role_segregation(self):
        """S04 | seguridad | administrador sin acceso tributario y operador sin administración"""
        self.assertEqual(self.client.get('/api/users').status_code,403)
        admin=self.application.test_client();self.login(admin,'admin')
        self.assertEqual(admin.get('/api/ratings').status_code,403);self.assertEqual(self.request('/api/ratings',payload=VALID,client=admin).status_code,403)
        self.assertEqual(admin.get('/api/users').status_code,200)
    def test_S05_sql_injection(self):
        """S05 | seguridad | consultas parametrizadas resisten payload de inyección"""
        self.assertEqual(self.client.get('/api/ratings',query_string={'q':"' OR 1=1 --"}).json['total'],0)
        self.assertEqual(len(self.sql('SELECT id FROM usuario')),4)
    def test_S06_xss_no_execution_inputs(self):
        """S06 | seguridad | validación rechaza script y CSP prohíbe scripts externos/inline"""
        self.assertEqual(self.request('/api/ratings',payload=dict(VALID,rating='<script>alert(1)</script>')).status_code,422)
        response=self.client.get('/');self.assertIn("script-src 'self'",response.headers['Content-Security-Policy']);self.assertNotIn(b'<script>alert',response.data)
    def test_S07_upload_restrictions(self):
        """S07 | seguridad | archivos de extensión no permitida y binarios rechazados"""
        self.assertEqual(self.preview(b'hello',filename='bad.exe').status_code,422)
        self.assertEqual(self.preview(b'\x00',filename='bad.csv').status_code,422)
        self.assertEqual(self.client.get('/data/private/anything.csv').status_code,404)
    def test_S08_private_files_cross_broker_hash(self):
        """S08 | seguridad | archivo privado rechaza corredor ajeno y modificación de contenido"""
        self.preview(self.csv(['SCL,2026-10,FILE-DEMO,Demo,monto,1,2,,1']));file=self.client.get('/api/batches').json['items'][0]['files'][0]
        other=self.application.test_client();self.login(other,'operador_b');self.assertEqual(other.get('/api/files/'+str(file['id'])).status_code,404)
        internal=self.sql('SELECT nombre_interno FROM archivo WHERE id=?',(file['id'],))[0][0]
        (Path(self.application.config['PRIVATE'])/internal).write_bytes(b'changed')
        self.assertEqual(self.client.get('/api/files/'+str(file['id'])).status_code,409)
    def test_S09_audit_appendonly(self):
        """S09 | seguridad | triggers rechazan edición/borrado y cadena HMAC es válida"""
        self.create()
        for sql in ["UPDATE evento_auditoria SET accion='fake' WHERE id=1",'DELETE FROM evento_auditoria WHERE id=1']:
            with self.assertRaises(sqlite3.IntegrityError):self.sql(sql)
        self.assertTrue(self.client.get('/api/audit').json['integrity'])
    def test_S10_profile_revocation_audit_scope(self):
        """S10 | seguridad | revocar corredor retira consulta y auditoría del ámbito anterior"""
        self.create();admin=self.application.test_client();self.login(admin,'admin')
        change=self.request('/api/users/1','put',dict(role='operador',active=True,brokers=[2],version=1),client=admin)
        self.assertEqual(change.status_code,200);self.assertEqual(self.client.get('/api/ratings').json['items'][0]['corredor_id'],2)
        self.assertEqual(self.client.get('/api/audit').json['items'],[])
    def test_S11_malformed_json(self):
        """S11 | seguridad | JSON no objeto devuelve error controlado, no 500"""
        for payload in [[],[1], 'text', None]:
            response=self.client.post('/api/ratings',json=payload,headers={'X-CSRF-Token':self.token()});self.assertEqual(response.status_code,400)
    def test_S12_expiry_logout_cookie(self):
        """S12 | seguridad | sesión expirada, cierre y cookie HttpOnly/SameSite"""
        with self.client.session_transaction() as s:s['last']=time.time()-1900
        self.assertEqual(self.client.get('/api/ratings').status_code,401)
        self.login(self.client);response=self.request('/api/logout');self.assertEqual(response.status_code,200);self.assertEqual(self.client.get('/api/ratings').status_code,401)
        cookie=response.headers.get('Set-Cookie','');self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=Strict',cookie)
    def test_S13_login_rate_limit(self):
        """S13 | seguridad | bloqueo temporal luego de cinco fallos de acceso"""
        client=self.application.test_client()
        for n in range(5):self.assertEqual(self.request('/api/login',payload=dict(login='nobody',password='bad'),client=client).status_code,401)
        self.assertEqual(self.request('/api/login',payload=dict(login='nobody',password='bad'),client=client).status_code,429)
    def test_S14_supervisor_assigned_brokers(self):
        """S14 | seguridad | supervisor consulta solamente corredores asignados"""
        sup=self.application.test_client();self.login(sup,'supervisor');self.assertEqual(sup.get('/api/ratings').json['total'],3)
        self.assertEqual(self.request('/api/ratings',payload=dict(VALID,broker=2),client=sup).status_code,201)
    def test_P01_twenty_clients_query(self):
        """P01 | rendimiento | 20 clientes concurrentes, P95 de consulta <=3 s y sin 5xx"""
        clients=[]
        for _ in range(20):
            client=self.application.test_client();self.login(client);clients.append(client)
        barrier=Barrier(20)
        def work(client):
            barrier.wait();start=time.perf_counter();response=client.get('/api/ratings');return time.perf_counter()-start,response.status_code
        with ThreadPoolExecutor(max_workers=20) as executor:measurements=list(executor.map(work,clients))
        times=sorted(m[0] for m in measurements);p95=times[18];codes=[m[1] for m in measurements]
        METRICS['P01']=dict(clients=20,requests=20,p95_seconds=round(p95,6),max_seconds=round(max(times),6),http_statuses=codes,scope='Flask test_client local; no red ni entorno NUAM')
        self.assertLessEqual(p95,3);self.assertTrue(all(c==200 for c in codes))
    def test_P02_thousand_rows_memory(self):
        """P02 | rendimiento | prevalidar/confirmar 1000 filas <=120 s con memoria medida"""
        rows=[f'SCL,2026-10,PERF-{n},Demo,monto,1,2,,1' for n in range(1000)]
        tracemalloc.start();start=time.perf_counter();preview=self.preview(self.csv(rows));self.assertEqual(preview.status_code,200)
        response=self.request(f"/api/batches/{preview.json['id']}/confirm");elapsed=time.perf_counter()-start
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        METRICS['P02']=dict(rows=1000,elapsed_seconds=round(elapsed,6),peak_python_bytes=peak,current_python_bytes=current,inserted=response.json.get('inserted'),scope='Flask test_client + SQLite + filesystem privado local; memoria Python, no RAM total ni nube NUAM')
        self.assertEqual(response.status_code,200);self.assertEqual(response.json['inserted'],1000);self.assertLessEqual(elapsed,120)

if __name__=='__main__':unittest.main(verbosity=2)
