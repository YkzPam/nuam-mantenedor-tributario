"""Motor documental TinyDB para reportes derivados; solo un proceso local.

Un RLock serializa accesos del servidor threaded. SQLite sigue siendo la fuente
de verdad operativa. No se promete ACID distribuida ni soporte multiproceso.
"""
from pathlib import Path
from threading import RLock
from contextlib import contextmanager
import json
from tinydb import TinyDB, Query

LOCK=RLock()

class DocumentStoreError(RuntimeError):
    pass

@contextmanager
def open_documents(private):
    try:
        with LOCK, TinyDB(Path(private)/'reportes.tinydb.json',encoding='utf-8',ensure_ascii=False) as database:
            yield database.table('reportes')
    except (OSError,json.JSONDecodeError,ValueError,TypeError,KeyError,AttributeError) as error:
        raise DocumentStoreError('El repositorio documental no está disponible o no supera su lectura.') from error

def upsert_report(private,batch,report,sha256):
    document=dict(batch_id=batch['id'],broker_id=batch['corredor_id'],owner_id=batch['usuario_id'],
        kind=batch['tipo'],state=batch['estado'],created_utc=batch['creado'],source_sha256=sha256,
        classification='Documento académico derivado; datos ficticios',report=report)
    with open_documents(private) as table:
        table.upsert(document,Query().batch_id==batch['id'])

def remove_report(private,batch_id):
    with open_documents(private) as table:
        table.remove(Query().batch_id==batch_id)

def report_by_batch(private,batch_id):
    with open_documents(private) as table:
        document=table.get(Query().batch_id==batch_id)
        return dict(document) if document is not None else None

def reports_for_brokers(private,broker_ids):
    with open_documents(private) as table:
        items=table.search(Query().broker_id.one_of(broker_ids))
        return [dict(item) for item in sorted(items,key=lambda item:item['batch_id'],reverse=True)[:30]]

def update_state(private,batch_id,state):
    with open_documents(private) as table:
        table.update(dict(state=state),Query().batch_id==batch_id)
