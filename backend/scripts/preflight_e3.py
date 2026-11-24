"""Chequeo reproducible sin secretos: HTTP reales, solo diagnóstico previo."""
from datetime import datetime, timezone
from pathlib import Path
import json
import time
import urllib.request
import urllib.error
import uuid

ROOT = Path(__file__).resolve().parents[2]
url_list = [
    ('gateway', 'http://127.0.0.1:8000/health', [200]),
    ('catalogo_publico', 'http://127.0.0.1:8000/api/public/products', [200]),
    ('frontend', 'http://127.0.0.1:8080/registro.php', [200]),
    ('verificacion_correo', 'http://127.0.0.1:8080/verificar-correo.php', [200]),
    ('sin_sesion', 'http://127.0.0.1:8000/api/orders', [401]),
]
results=[]
for label,url,expected in url_list:
    operacion_id=str(uuid.uuid4())
    req=urllib.request.Request(url)
    started=time.monotonic()
    try:
        with urllib.request.urlopen(req,timeout=12) as response:
            code=response.status; correlation=response.headers.get('X-Operacion')
    except urllib.error.HTTPError as error:
        code=error.code; correlation=error.headers.get('X-Operacion')
    except (OSError,TimeoutError) as error:
        code=None;correlation=None
    elapsed=round((time.monotonic()-started)*1000,1)
    ok=code in expected
    results.append({'id':label,'expected_http':expected,'observed_http':code,'ok':ok,'elapsed_ms':elapsed,'operacion_id':correlation or operacion_id})
    print(f'{"OK" if ok else "FALLO"}  {label:18} HTTP={code} esperado={expected} {elapsed}ms')
output={
    'ejecucion':str(uuid.uuid4()),'fecha_utc':datetime.now(timezone.utc).isoformat(),
    'tipo':'Comprobación de conectividad; NO prueba E2E de persistencia ni permisos',
    'resultados':results
}
folder=ROOT/'docs/evaluacion/evidencias'
folder.mkdir(exist_ok=True,parents=True)
path=folder/('preflight_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')
path.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
print('Registro:',path.relative_to(ROOT))
raise SystemExit(0 if all(x['ok'] for x in results) else 1)
