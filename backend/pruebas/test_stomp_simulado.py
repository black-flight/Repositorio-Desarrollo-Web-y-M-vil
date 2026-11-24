"""Contrato productor/consumidor STOMP con broker en memoria simulado, NO ActiveMQ real."""
import importlib
import json
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))

mensajes=[]
class Connection:
    def __init__(self,*args,**kwargs):self.connected=False;self.acks=[]
    def connect(self,*args,**kw):self.connected=True
    def send(self,destination,body,headers):mensajes.append((destination,json.loads(body),headers))
    def is_connected(self):return self.connected
    def disconnect(self):self.connected=False
    def ack(self,*args,**kwargs):self.acks.append(kwargs)
class Listener:pass
stomp=types.ModuleType('stomp')
stomp.Connection12=Connection
stomp.ConnectionListener=Listener
sys.modules['stomp']=stomp
class DuplicateKeyError(Exception):pass
pymongo=types.ModuleType('pymongo')
errors=types.ModuleType('pymongo.errors');errors.DuplicateKeyError=DuplicateKeyError
pymongo.errors=errors
pymongo.MongoClient=object
sys.modules['pymongo']=pymongo;sys.modules['pymongo.errors']=errors
productor=importlib.import_module('backend.mensajeria.productor')
consumidor=importlib.import_module('backend.mensajeria.consumidor')

class Col:
    def __init__(self):self.docs={}
    def create_index(self,*args,**kwargs):pass
    def insert_one(self,ev):
        if ev['event_id'] in self.docs:raise DuplicateKeyError('duplicado')
        self.docs[ev['event_id']]=dict(ev)
class Mongo(dict):
    def __getitem__(self,key):
        if key not in self:self[key]={'events_consumed':Col()}
        return dict.__getitem__(self,key)

def main():
    pedido={'id':'ORD-TEST-1','estado':'pagado','total':12000,'modalidad':'retiro','referencia_pago':'PAY-TEST'}
    productor.publicar_pedido_pagado(pedido,'operacion-123456')
    assert mensajes[0][0]=='/queue/tokyo.orders'
    ev=mensajes[0][1]
    assert ev['event_type']=='order.paid' and ev['order_id']=='ORD-TEST-1' and ev['total_clp']==12000
    try:productor.publicar_pedido_pagado({**pedido,'estado':'pendiente_pago'},'operacion-123456')
    except ValueError:pass
    else:raise AssertionError('No debe publicar antes de pagar')
    m=Mongo();conn=Connection()
    listener=consumidor.Consumer(conn,m)
    frame=SimpleNamespace(body=json.dumps(ev),headers={'ack':'msg-1','subscription':'tokyo-consumer'})
    listener.on_message(frame);listener.on_message(frame)
    assert len(m['tokyo_noodles_eval2']['events_consumed'].docs)==1
    assert len(conn.acks)==2
    print('STOMP aislado: evento real por pedido pagado, rechazo previo a pago y deduplicación event_id OK (broker SIMULADO).')
if __name__=='__main__':main()
