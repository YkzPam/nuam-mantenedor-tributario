"""Prueba de humo del contenedor: sesión, CSRF, catálogo, escritura y persistencia tras reiniciar."""
import json, subprocess, sys, time, urllib.request, http.cookiejar
BASE='http://127.0.0.1:8765'
def client():
    cj=http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.ProxyHandler({}),urllib.request.HTTPCookieProcessor(cj))
def call(op,method,path,body=None,csrf=None):
    req=urllib.request.Request(BASE+path,method=method,data=None if body is None else json.dumps(body).encode(),
        headers={'Content-Type':'application/json',**({'X-CSRF-Token':csrf} if csrf else {})})
    try:
        with op.open(req,timeout=10) as r: return r.status,json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e: return e.code,json.loads(e.read() or b'{}')
def wait():
    for _ in range(40):
        try:
            urllib.request.build_opener(urllib.request.ProxyHandler({})).open(BASE+'/',timeout=2); return
        except Exception: time.sleep(0.5)
    sys.exit('el contenedor no respondió')
res=[]
def check(name,ok,detail): res.append(dict(prueba=name,ok=bool(ok),detalle=detail)); print(('OK  ' if ok else 'FALLA ')+name+' | '+detail)
wait(); op=client()
s,me=call(op,'GET','/api/me'); csrf=me.get('csrf')
s,_=call(op,'POST','/api/login',dict(login='supervisor',password='Demo2026!'),csrf=None)
check('Login sin token CSRF rechazado',s==403,f'HTTP {s}')
s,_=call(op,'POST','/api/login',dict(login='supervisor',password='Demo2026!'),csrf=csrf)
check('Login de supervisor con CSRF',s==200,f'HTTP {s}')
s,me=call(op,'GET','/api/me'); csrf=me['csrf']
s,d=call(op,'GET','/api/instruments?q=DEMO-SUSPENDIDO')
items=d.get('items',d if isinstance(d,list) else [])
check('Catálogo semilla visible',s==200 and any(i.get('codigo')=='DEMO-SUSPENDIDO' for i in items),f'HTTP {s}, {len(items)} resultado(s)')
code='DEMO-DOCKER-'+time.strftime('%H%M%S')
s,d=call(op,'POST','/api/instruments',dict(market='SCL',code=code,registered=1),csrf=csrf)
check('Alta de instrumento por supervisor',s in (200,201),f'HTTP {s}, código {code}')
op2=client(); s,me2=call(op2,'GET','/api/me'); call(op2,'POST','/api/login',dict(login='operador_a',password='Demo2026!'),csrf=me2['csrf'])
s,me2=call(op2,'GET','/api/me')
s,_=call(op2,'POST','/api/instruments',dict(market='SCL',code=code+'X',registered=1),csrf=me2['csrf'])
check('Operador no puede modificar el catálogo',s==403,f'HTTP {s}')
subprocess.run(['docker','restart','nuam'],check=True,capture_output=True); wait()
op3=client(); s,me3=call(op3,'GET','/api/me'); call(op3,'POST','/api/login',dict(login='supervisor',password='Demo2026!'),csrf=me3['csrf'])
s,d=call(op3,'GET','/api/instruments?q='+code)
items=d.get('items',d if isinstance(d,list) else [])
check('El dato persiste en el volumen tras reiniciar',s==200 and any(i.get('codigo')==code for i in items),f'HTTP {s}, {len(items)} resultado(s)')
json.dump(res,open(sys.argv[1],'w',encoding='utf8'),ensure_ascii=False,indent=2)
sys.exit(0 if all(r['ok'] for r in res) else 1)
