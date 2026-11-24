"""Pruebas ASGI aisladas de Orders con Mongo/HTTP/STOMP simulados.
NO comprueban broker ni base de datos reales; para eso usar Docker y evidencia.
"""
import asyncio
import copy
import importlib.util
import json
import os
import sys
import types
import uuid
from pathlib import Path
from types import SimpleNamespace

import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ['INTERNAL_GATEWAY_SECRET'] = 'demo-internal-secret-solo-test'
os.environ['PAYMENTS_TO_ORDERS_SECRET'] = 'demo-payments-secret-solo-test'
os.environ['DELIVERY_STORE_LAT'] = '-33.51'
os.environ['DELIVERY_STORE_LON'] = '-70.75'

class DuplicateKeyError(Exception):pass
class ReturnDocument:
    AFTER = True

class Collection:
    def __init__(self):
        self.docs=[];self.lock=asyncio.Lock();self.indices=[]
    def _matches(self,d,q):
        for key,val in q.items():
            v=d.get(key)
            if isinstance(val,dict) and '$in' in val:
                if v not in val['$in']:return False
            elif v!=val:return False
        return True
    def _project(self,d,fields=None):
        if d is None:return None
        x=copy.deepcopy(d)
        if fields:
            for key,v in fields.items():
                if v==0:x.pop(key,None)
        return x
    async def create_index(self,*a,**kw):self.indices.append((a,kw))
    async def find_one(self,q,fields=None):
        async with self.lock:
            d=next((x for x in self.docs if self._matches(x,q)),None)
            return self._project(d,fields)
    async def insert_one(self,doc):
        async with self.lock:
            for existing in self.docs:
                if existing['id']==doc['id'] or (existing['client_id']==doc['client_id'] and existing.get('codigo_compra')==doc.get('codigo_compra')):
                    raise DuplicateKeyError('unique composite key collision')
            doc['_id']=str(uuid.uuid4());self.docs.append(copy.deepcopy(doc))
            return SimpleNamespace(inserted_id=doc['_id'])
    async def update_one(self,q,change):
        async with self.lock:
            for d in self.docs:
                if self._matches(d,q):
                    if '$set' in change:d.update(change['$set'])
                    return SimpleNamespace(modified_count=1,matched_count=1)
        return SimpleNamespace(modified_count=0,matched_count=0)
    async def find_one_and_update(self,q,change,return_document=None):
        async with self.lock:
            for d in self.docs:
                if self._matches(d,q):
                    d.update(change.get('$set',{}));return self._project(d)
        return None
    async def count_documents(self,q):
        async with self.lock:return sum(self._matches(d,q) for d in self.docs)

class Database:
    def __init__(self):self.collections={}
    def __getitem__(self,key):return self.collections.setdefault(key,Collection())

class FakeMongoClient:
    def __init__(self,*args,**kwargs):self.databases={};self.admin=SimpleNamespace(command=self.ping)
    async def ping(self,*args):return {'ok':1}
    def __getitem__(self,key):return self.databases.setdefault(key,Database())

fake_pymongo=types.ModuleType('pymongo')
fake_pymongo.ReturnDocument=ReturnDocument
fake_errors=types.ModuleType('pymongo.errors')
fake_errors.DuplicateKeyError=DuplicateKeyError
fake_pymongo.errors=fake_errors
fake_motor=types.ModuleType('motor')
fake_motor_asyncio=types.ModuleType('motor.motor_asyncio')
fake_motor_asyncio.AsyncIOMotorClient=FakeMongoClient
fake_stomp=types.ModuleType('stomp')
fake_stomp.Connection12=object
for name,module in [('pymongo',fake_pymongo),('pymongo.errors',fake_errors),('motor',fake_motor),('motor.motor_asyncio',fake_motor_asyncio),('stomp',fake_stomp)]:
    sys.modules[name]=module

spec=importlib.util.spec_from_file_location('orders_simulados',ROOT/'backend/orders/backend_api.py')
orders=importlib.util.module_from_spec(spec);spec.loader.exec_module(orders)

class HTTPResponse:
    def __init__(self,code,body):self.status_code=code;self.body=body
    def json(self):return self.body
class FakeHTTP:
    async def __aenter__(self):return self
    async def __aexit__(self,*args):return False
    async def get(self,url,headers):
        if '/clients/' in url:return HTTPResponse(200,{'activo':True,'correo_verificado':False})
        if '/products/' in url:return HTTPResponse(200,{'id':'1','nombre':'Shio Ramen','precio':13800,'available':True})
        raise AssertionError(url)
orders.httpx=SimpleNamespace(AsyncClient=lambda **kw:FakeHTTP(),RequestError=httpx.RequestError)

sent=[]
def fake_send(pedido,operacion_id):
    sent.append((pedido['id'],operacion_id))
orders.publicar_pedido_pagado=fake_send
HEADERS={'X-Gateway-Secret':os.environ['INTERNAL_GATEWAY_SECRET'],
         'X-Authenticated-Client':'USR-001','X-Authenticated-Roles':'user'}

async def main():
    await orders.inicializar_indices()
    assert orders.pedidos_db.indices and 'codigo_compra' in str(orders.pedidos_db.indices)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=orders.app),base_url='http://orders.test') as cliente:
        body={'codigo_compra':str(uuid.uuid4()),'modalidad':'retiro','items':[{'product_id':'1','quantity':2}]}
        async def call(method,path,**kw):return await cliente.request(method,path,headers=HEADERS,**kw)
        uno=await call('POST','/orders',json=body)
        assert uno.status_code==201,uno.text
        pedido=uno.json()
        assert pedido['total']==27600 and pedido['estado']=='pendiente_pago'
        assert not sent, 'no se publica antes del pago'
        dos=await call('POST','/orders',json=body)
        assert dos.status_code==200 and dos.json()['id']==pedido['id']
        conflicto=await call('POST','/orders',json={**body,'items':[{'product_id':'1','quantity':1}]})
        assert conflicto.status_code==409,conflicto.text
        nueva={**body,'codigo_compra':str(uuid.uuid4())}
        ambos=await asyncio.gather(call('POST','/orders',json=nueva),call('POST','/orders',json=nueva))
        assert sorted(x.status_code for x in ambos)==[200,201],[(x.status_code,x.text) for x in ambos]
        assert ambos[0].json()['id']==ambos[1].json()['id']
        assert await orders.pedidos_db.count_documents({'codigo_compra':nueva['codigo_compra']})==1
        pago=await cliente.post('/orders/'+pedido['id']+'/confirm-payment',
            headers={**HEADERS,'X-Authenticated-Client':'payments-service',
                     'X-Authenticated-Roles':'payments','X-Payments-Secret':os.environ['PAYMENTS_TO_ORDERS_SECRET']},
            json={'referencia':'PAY-PRUEBA'})
        assert pago.status_code==200,pago.text
        assert pago.json()['estado']=='pagado' and sent and sent[0][0]==pedido['id']
        again=await cliente.post('/orders/'+pedido['id']+'/confirm-payment',
            headers={**HEADERS,'X-Authenticated-Client':'payments-service',
                     'X-Authenticated-Roles':'payments','X-Payments-Secret':os.environ['PAYMENTS_TO_ORDERS_SECRET']},
            json={'referencia':'PAY-PRUEBA'})
        assert again.status_code==200 and len(sent)==1
        outside=await call('POST','/orders',json={**body,'codigo_compra':str(uuid.uuid4()),'modalidad':'delivery',
            'direccion':'Calle ficticia 100','latitude':-33.56,'longitude':-70.75})
        assert outside.status_code==422
        sinpermiso=await call('POST','/orders/'+pedido['id']+'/publish-event')
        assert sinpermiso.status_code==403
    print('Orders ASGI aislado: 201/200 reintento, 409 payload, 2 concurrentes -> 1 pedido,')
    print('total calculado, STOMP después del pago, referencia repetida, delivery 422 y permisos OK (mocks; NO Mongo ni STOMP reales).')

if __name__=='__main__':asyncio.run(main())
