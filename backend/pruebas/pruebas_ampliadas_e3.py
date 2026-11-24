"""E3 ampliada. Pruebas HTTP REALES; no muestra ni persiste contraseñas/tokens.

Ejecutar después de `docker compose up -d --build`.
Crea clientes y pedidos FICTICIOS; registrar esta ejecución separada de E2.
"""
import getpass
import json
import os
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT=Path(__file__).resolve().parents[2]
ENDPOINT=os.getenv('TOKYO_API_BASE_URL','http://127.0.0.1:8000/api').rstrip('/')
report=[]
client=httpx.Client(timeout=15)

def call(method,path,token=None,**kwargs):
    headers=dict(kwargs.pop('headers',{}) or {})
    headers['X-Operacion']=str(uuid.uuid4())
    if token:headers['Authorization']='Bearer '+token
    return client.request(method,ENDPOINT+path,headers=headers,**kwargs)

def record(id_,title,expected,response=None,details='',blocked=False):
    if blocked: status='BLOQUEADA'
    elif response is None:status='FALLIDA'
    else:status='APROBADA' if response.status_code in expected else 'FALLIDA'
    one={'id':id_,'descripcion':title,'estado':status,
         'esperado_http':expected,'observado_http':getattr(response,'status_code',None),
         'operacion_id':response.headers.get('X-Operacion') if response else None,'observacion':details}
    report.append(one)
    print(f'[{status}] {id_} · {title} HTTP={one["observado_http"]} esperado={expected} {details}')
    return status=='APROBADA'

def unique_profile():
    suffix=secrets.token_hex(4)
    password=secrets.token_urlsafe(16)
    return {'username':'demo'+suffix,'password':password,
         'run':'RUN-FICTICIO-'+suffix,'nombre':'Cliente Ficticio '+suffix,
         'direccion':'Calle Ficticia 100','comuna':'Maipú','provincia':'Santiago',
         'region':'Metropolitana','fecha_nacimiento':'1995-01-01','sexo':'X',
         'correo':'prueba'+suffix+'@example.test','telefono':'000000000'}

def store_coords():
    path=ROOT/'.env'
    if not path.exists():return None
    lines=dict(x.split('=',1) for x in path.read_text().splitlines() if '=' in x and not x.startswith('#'))
    try:return float(lines['DELIVERY_STORE_LAT']),float(lines['DELIVERY_STORE_LON'])
    except (ValueError,KeyError):return None

def main():
    adminpass=getpass.getpass('Contraseña admin de ernesto (vacío = pruebas admin bloqueadas): ')
    user=unique_profile()
    token=None;admin=None;order=None;payment=None
    try:
        r=call('POST','/auth/register',json=user)
        if record('P15','Alta Auth + perfil Clients', [201],r):
            identity=r.json()['user_id']
            r=call('POST','/auth/login',json={'username':user['username'],'password':user['password']})
            if record('P16','Login del nuevo usuario', [200],r):token=r.json()['access_token']
            if token:
                r=call('GET','/clients/'+identity,token)
                record('P17','Perfil persistente propio', [200],r, 'id_coincide='+str(r.json().get('id')==identity) if r.status_code==200 else '')
        else:
            record('P16','Login nuevo usuario',[200],blocked=True)
            record('P17','Perfil propio',[200],blocked=True)

        if token:
            r=call('GET','/clients/'+identity)
            record('P18','Perfil sin sesión rechazado',[401],r)
            r=call('PUT','/orders/ORD-INVALID/status',token,json={'estado':'en_preparacion'})
            record('P19','Cliente no puede administrar estados',[403],r)
            idem=str(uuid.uuid4())
            datos={'codigo_compra':idem,'modalidad':'retiro','items':[{'product_id':'1','quantity':1}]}
            r=call('POST','/orders',token,json=datos,)
            if record('P20','Creación de pedido en Orders',[201],r):
                order=r.json()
                r=call('POST','/orders',token,json=datos,)
                ok=record('P21','Código de compra en Mongo (reintento)',[200],r, 'mismo_id='+str(r.json().get('id')==order['id']) if r.status_code==200 else '')
                r=call('POST','/orders',token,json={**datos,'items':[{'product_id':'1','quantity':2}]},)
                record('P22','Código de compra rechaza contenido distinto',[409],r)
                r=call('GET','/orders/'+order['id'],token)
                record('P23','Lectura independiente de persistencia',[200],r)
                r=call('POST','/payments',token,json={'order_id':order['id']})
                if record('P24','Solicitud de pago vinculada a Orders',[201],r):
                    payment=r.json()
                    r=call('POST','/payments',token,json={'order_id':order['id']})
                    record('P25','Unicidad de pago por pedido',[200,201],r,'mismo_id='+str(r.json().get('id')==payment['id']) if r.status_code in [200,201] else '')
                    r=call('POST','/payments/'+payment['id']+'/test-confirm',token,json={})
                    record('P26','Usuario no confirma pagos de prueba',[403],r)
            else:
                for id_,msg in [('P21','Duplicados'),('P22','Conflicto de clave'),('P23','Persistencia'),('P24','Pago'),('P25','Pago repetido'),('P26','Rol de pago')]:
                    record(id_,msg,[200],blocked=True)
            coords=store_coords()
            if coords:
                lat,lon=coords
                d={'codigo_compra':str(uuid.uuid4()), 'modalidad':'delivery','direccion':'Domicilio ficticio cerca de la sucursal',
                   'items':[{'product_id':'1','quantity':1}], 'latitude':lat+0.06,'longitude':lon}
                r=call('POST','/orders',token,json=d,)
                record('P27','Fuera de radio 3 km rechazado',[422],r)
                d['latitude']=lat+0.01
                d['codigo_compra']=str(uuid.uuid4())
                r=call('POST','/orders',token,json=d,)
                record('P28','Dentro de radio 3 km crea pedido',[201],r)
            else:
                record('P27','Fuera de radio 3 km',[422],blocked=True)
                record('P28','Dentro de radio 3 km',[201],blocked=True)
            if order:
                # Dos compras concurrentes con el mismo código; misma identidad y payload.
                from concurrent.futures import ThreadPoolExecutor
                con={'codigo_compra':str(uuid.uuid4()), 'modalidad':'retiro','items':[{'product_id':'1','quantity':1}]}
                with ThreadPoolExecutor(max_workers=2) as pool:
                    futuras=[pool.submit(call,'POST','/orders',token,json=con) for _ in range(2)]
                    respuestas=[f.result() for f in futuras]
                codigos=sorted(x.status_code for x in respuestas)
                ids=[x.json().get('id') if x.status_code in [200,201] else None for x in respuestas]
                ok=codigos==[200,201] and bool(ids[0]) and ids[0]==ids[1]
                r_con=call('GET','/orders',token)
                coincidencias = [x for x in r_con.json().get('orders',[]) if x.get('codigo_compra')==con['codigo_compra']] if r_con.status_code==200 else []
                ok = ok and len(coincidencias)==1
                record('P39','Compras concurrentes un solo documento',[200,201] if ok else [299],respuestas[0],
                       details='concurrent_status='+str(codigos)+' mismo_id='+str(ids[0]==ids[1])+ ' documentos='+str(len(coincidencias)))
                query='query Resumen($id: ID!) { resumenPedido(id:$id){ id estado total items { productId disponibleActual } advertencias } }'
                r=call('POST','/graphql',token,json={'query':query,'variables':{'id':order['id']}})
                record('P29','Lectura GraphQL Orders + Inventory',[200],r)
            else:record('P29','Lectura GraphQL',[200],blocked=True)
        else:
            for j in range(18,30):record('P'+str(j),'Requiere usuario registrado',[200],blocked=True)

        if adminpass:
            r=call('POST','/auth/login',json={'username':'ernesto','password':adminpass})
            if record('P30','Login administrativo',[200],r):admin=r.json()['access_token']
        else:record('P30','Login administrativo',[200],blocked=True)
        if admin and payment and order:
            r=call('POST','/payments/'+payment['id']+'/test-confirm',admin,json={})
            record('P31','Confirmación simulada de pago protegida',[200],r)
            r=call('GET','/orders/'+order['id'],token)
            record('P32','Persistencia del estado pagado',[200],r,'estado='+r.json().get('estado','?') if r.status_code==200 else '')
            r=call('GET','/orders/'+order['id']+'/comprobante',token)
            record('P33','Comprobante comercial no tributario',[200],r,
                    'tipo='+r.json().get('tipo','?') if r.status_code==200 else '')
            today=datetime.now(timezone.utc).date().isoformat()
            r=call('GET','/orders/reporte-ventas?desde='+today+'&hasta='+today,admin)
            record('P34','Reporte de ventas de administrador',[200],r)
            r=call('GET','/orders/eventos',admin)
            record('P35','Estado del publicador ActiveMQ',[200],r)
        else:
            for id_,msg in [('P31','Pago de prueba'),('P32','Persistencia pagado'),('P33','Comprobante'),('P34','Reporte'),('P35','Estado mensajería')]:
                record(id_,msg,[200],blocked=True)

        if token:
            r=call('POST','/auth/logout',token,json={})
            record('P36','Logout cuenta nueva',[200],r)
            r=call('GET','/auth/me',token)
            record('P37','Revocación efectiva',[401],r)
        else:
            record('P36','Logout',[200],blocked=True)
            record('P37','Revocación',[401],blocked=True)
    except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print('Ejecución interrumpida:',type(exc).__name__,str(exc)[:180])
        record('P-INTERRUMPIDA','Error de transporte o contrato',[200],details=type(exc).__name__)
    finally:
        client.close()
        user['password']=''
        adminpass=''
        folder=ROOT/'docs/evaluacion/evidencias';folder.mkdir(parents=True,exist_ok=True)
        output={
            'evaluacion':'E3 ampliada','run_id':str(uuid.uuid4()),
            'fecha_utc':datetime.now(timezone.utc).isoformat(),
            'tipo':'HTTP real contra servicios iniciados, no sustituye E2E desde navegador',
            'version':'Adjuntar commit o hash de ZIP al registro de la ejecución',
            'resultados':report,
            'conteos':{s:sum(x['estado']==s for x in report) for s in ('APROBADA','FALLIDA','BLOQUEADA')}
        }
        path=folder/('run_ampliada_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')
        path.write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
        print('\nSe guardaron resultados observados sin credenciales:',path.relative_to(ROOT))
        print('Resumen:',output['conteos'])
    return 0 if all(x['estado']=='APROBADA' for x in report) else 1

if __name__=='__main__':
    raise SystemExit(main())
