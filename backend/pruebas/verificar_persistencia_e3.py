"""Comprobación read-only de Mongo real desde Docker.
Ejemplo: docker compose exec orders python -m backend.pruebas.verificar_persistencia_e3 --pedido ORD-XXXX
No imprime datos personales ni secretos.
"""
import argparse
import os
from pymongo import MongoClient

p=argparse.ArgumentParser()
p.add_argument('--pedido',default=None)
a=p.parse_args()
base=MongoClient(os.environ['MONGO_URL'],serverSelectionTimeoutMS=3000)['tokyo_noodles_eval2']
base.client.admin.command('ping')
print('mongo=connected (real)')
for tabla in ('orders','payments','clients','notifications','email_verifications','events_consumed'):
    print('coleccion=%s total=%s'%(tabla,base[tabla].count_documents({})))
indices=base['orders'].index_information()
print('indices_ordenes=',{x:str(v.get('key')) for x,v in indices.items()})
if a.pedido:
    o=base['orders'].find_one({'id':a.pedido},{'_id':0,'id':1,'estado':1,'event_status':1,'referencia_pago':1,'codigo_compra':1})
    pago=base['payments'].find_one({'order_id':a.pedido},{'_id':0,'id':1,'estado':1})
    eventos=base['events_consumed'].count_documents({'order_id':a.pedido,'event_type':'order.paid'})
    print('pedido=',o,'pago=',pago,'eventos_consumidos=',eventos)
    if not o:raise SystemExit('pedido no encontrado')
