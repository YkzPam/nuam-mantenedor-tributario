PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS rol (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE CHECK(nombre IN ('operador','supervisor','administrador'))
);
CREATE TABLE IF NOT EXISTS corredor (
 id INTEGER PRIMARY KEY, codigo TEXT NOT NULL UNIQUE, nombre TEXT NOT NULL, activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0,1))
);
CREATE TABLE IF NOT EXISTS usuario (
 id INTEGER PRIMARY KEY, nombre TEXT NOT NULL, login TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL,
 rol_id INTEGER NOT NULL REFERENCES rol(id), activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0,1)), version INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS usuario_corredor (
 usuario_id INTEGER NOT NULL REFERENCES usuario(id), corredor_id INTEGER NOT NULL REFERENCES corredor(id),
 PRIMARY KEY(usuario_id, corredor_id)
);
CREATE TABLE IF NOT EXISTS regla_factor (
 id INTEGER PRIMARY KEY, version TEXT NOT NULL UNIQUE, descripcion TEXT NOT NULL,
 parametros_json TEXT NOT NULL CHECK(json_valid(parametros_json)), aprobada_nuam INTEGER NOT NULL CHECK(aprobada_nuam=0)
);
CREATE TABLE IF NOT EXISTS calificacion (
 id INTEGER PRIMARY KEY, corredor_id INTEGER NOT NULL REFERENCES corredor(id), mercado TEXT NOT NULL CHECK(mercado IN ('SCL','COL','LIM')),
 periodo TEXT NOT NULL, instrumento TEXT NOT NULL, calificacion TEXT NOT NULL, inscrito INTEGER NOT NULL CHECK(inscrito IN (0,1)),
 monto TEXT, base TEXT, factor TEXT NOT NULL, origen TEXT NOT NULL CHECK(origen IN ('manual','DJ1948-DEMO','factores-DEMO')),
 regla_id INTEGER REFERENCES regla_factor(id), activo INTEGER NOT NULL DEFAULT 1 CHECK(activo IN (0,1)),
 version INTEGER NOT NULL DEFAULT 1, creado TEXT NOT NULL, actualizado TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_calificacion_provisional ON calificacion(corredor_id, mercado, periodo, instrumento, calificacion) WHERE activo=1;
CREATE INDEX IF NOT EXISTS ix_calificacion_busqueda ON calificacion(corredor_id, activo, periodo, mercado);
CREATE TABLE IF NOT EXISTS carga (
 id INTEGER PRIMARY KEY, corredor_id INTEGER NOT NULL REFERENCES corredor(id), usuario_id INTEGER NOT NULL REFERENCES usuario(id),
 tipo TEXT NOT NULL CHECK(tipo IN ('DJ1948-DEMO','factores-DEMO')), estado TEXT NOT NULL CHECK(estado IN ('lista','rechazada','confirmada','conflicto')),
 total INTEGER NOT NULL, validas INTEGER NOT NULL, invalidas INTEGER NOT NULL, creado TEXT NOT NULL,
 confirmado TEXT, token TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS archivo (
 id INTEGER PRIMARY KEY, carga_id INTEGER NOT NULL REFERENCES carga(id), clase TEXT NOT NULL CHECK(clase IN ('original','reporte')),
 nombre_original TEXT NOT NULL, nombre_interno TEXT NOT NULL UNIQUE, tipo TEXT NOT NULL, bytes INTEGER NOT NULL CHECK(bytes>=0),
 sha256 TEXT NOT NULL CHECK(length(sha256)=64), creado TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS carga_fila (
 id INTEGER PRIMARY KEY, carga_id INTEGER NOT NULL REFERENCES carga(id), numero INTEGER NOT NULL,
 datos_json TEXT NOT NULL CHECK(json_valid(datos_json)), errores_json TEXT NOT NULL CHECK(json_valid(errores_json)),
 calificacion_id INTEGER REFERENCES calificacion(id), UNIQUE(carga_id,numero)
);
CREATE TABLE IF NOT EXISTS evento_auditoria (
 id INTEGER PRIMARY KEY, usuario_id INTEGER REFERENCES usuario(id), corredor_id INTEGER REFERENCES corredor(id),
 entidad TEXT NOT NULL, registro_id INTEGER, accion TEXT NOT NULL, fecha TEXT NOT NULL,
 antes_json TEXT CHECK(antes_json IS NULL OR json_valid(antes_json)), despues_json TEXT CHECK(despues_json IS NULL OR json_valid(despues_json)),
 resultado TEXT NOT NULL, hash_anterior TEXT NOT NULL, hash_evento TEXT NOT NULL UNIQUE
);
CREATE TRIGGER IF NOT EXISTS auditoria_no_update BEFORE UPDATE ON evento_auditoria BEGIN SELECT RAISE(ABORT,'La bitácora es de solo adición'); END;
CREATE TRIGGER IF NOT EXISTS auditoria_no_delete BEFORE DELETE ON evento_auditoria BEGIN SELECT RAISE(ABORT,'La bitácora es de solo adición'); END;
CREATE INDEX IF NOT EXISTS ix_logout_session_hash ON evento_auditoria(usuario_id,json_extract(despues_json,'$.session_hash')) WHERE accion='logout';
