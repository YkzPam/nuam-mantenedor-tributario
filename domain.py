"""Reglas de DEMOSTRACIÓN. Ninguna fórmula o llave tiene aprobación de NUAM."""
import csv
import io
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

CSV_COLUMNS = ['market','period','instrument','rating','mode','amount','base','factor','registered']
MAX_ROWS = 1000
MAX_FILE_BYTES = 500_000

class ValidationError(ValueError):
    pass

def decimal_value(value, label, maximum=Decimal('1000000000000')):
    try:
        text = str('' if value is None else value).strip()
        if not re.fullmatch(r'\d{1,13}(?:\.\d{1,6})?', text):
            raise InvalidOperation()
        number = Decimal(text)
        if not number.is_finite() or number < 0 or number > maximum:
            raise InvalidOperation()
        return number
    except (InvalidOperation, ValueError):
        raise ValidationError(f'{label}: usar un número no negativo, punto decimal y hasta 6 decimales.') from None

def factor_demo(amount, base):
    amount = decimal_value(amount, 'Monto')
    base = decimal_value(base, 'Base')
    if base <= 0 or amount > base:
        raise ValidationError('Base: debe ser mayor que cero y mayor o igual al monto.')
    return format((amount / base).quantize(Decimal('0.000001'), rounding=ROUND_HALF_UP), '.6f')

def required_text(data, field, label):
    # Do not turn JSON null, booleans or containers into apparently valid text.
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f'{label}: completar con texto válido; no se admiten valores nulos.')
    return value.strip()

def validate_rating(data):
    if not isinstance(data, dict):
        raise ValidationError('Registro: enviar un objeto con los campos requeridos.')
    market = required_text(data, 'market', 'Mercado').upper()
    period = required_text(data, 'period', 'Período')
    instrument = required_text(data, 'instrument', 'Instrumento').upper()
    rating = required_text(data, 'rating', 'Calificación')
    if market not in ('SCL','COL','LIM'):
        raise ValidationError('Mercado: seleccionar SCL, COL o LIM.')
    if not re.fullmatch(r'20\d{2}-(0[1-9]|1[0-2])', period):
        raise ValidationError('Período: usar AAAA-MM, entre 2000 y 2099.')
    if not re.fullmatch(r'[A-Z0-9][A-Z0-9._-]{0,39}', instrument):
        raise ValidationError('Instrumento: usar 1 a 40 letras, números, punto, guion o guion bajo.')
    if not re.fullmatch(r'[\wÁÉÍÓÚÜÑáéíóúüñ .-]{1,60}', rating, re.UNICODE):
        raise ValidationError('Calificación: usar 1 a 60 letras, números, espacios, punto o guion.')
    if str(data.get('registered','')) not in ('0','1'):
        raise ValidationError('Inscripción: seleccionar 1 (inscrito) o 0 (no inscrito).')
    mode = data.get('mode')
    if mode == 'monto':
        factor = factor_demo(data.get('amount'),data.get('base'))
        amount = format(decimal_value(data.get('amount'),'Monto'), 'f')
        base = format(decimal_value(data.get('base'),'Base'), 'f')
    elif mode == 'factor':
        factor = format(decimal_value(data.get('factor'),'Factor',Decimal('1')).quantize(Decimal('0.000001')), '.6f')
        amount = base = None
    else:
        raise ValidationError('Modo: seleccionar monto o factor.')
    return dict(mercado=market,periodo=period,instrumento=instrument,calificacion=rating,inscrito=int(data['registered']),
                monto=amount,base=base,factor=factor,regla_id=1 if mode=='monto' else None)

def business_key(row):
    return tuple(row[k] for k in ('mercado','periodo','instrumento','calificacion'))

def parse_csv(content):
    if not content or len(content)>MAX_FILE_BYTES:
        raise ValidationError('Archivo: vacío o superior a 500 KB.')
    try:
        text = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValidationError('Archivo: debe usar codificación UTF-8.') from None
    if any(ord(c)<32 and c not in '\n\r\t' for c in text) or '\x00' in text:
        raise ValidationError('Archivo: contiene caracteres de control o contenido binario.')
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames != CSV_COLUMNS:
        raise ValidationError('Encabezado incorrecto. Usar exactamente: '+','.join(CSV_COLUMNS))
    rows=[]
    try:
        for number, data in enumerate(reader,2):
            if len(rows)>=MAX_ROWS:
                raise ValidationError('Archivo: máximo 1000 filas de datos.')
            if None in data or any(v is None for v in data.values()):
                raise ValidationError(f'Fila {number}: cantidad de columnas incorrecta.')
            rows.append((number,data))
    except csv.Error:
        raise ValidationError('Archivo: estructura CSV inválida.') from None
    if not rows:
        raise ValidationError('Archivo: incluir al menos una fila de datos.')
    return rows
