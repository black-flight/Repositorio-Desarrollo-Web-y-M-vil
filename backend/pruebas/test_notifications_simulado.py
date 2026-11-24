"""Contrato HTTP del adaptador de correo; TODOS los envíos son simulados."""
import asyncio
import os
import sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.common import notifications

class Col:
    def __init__(self):self.docs=[]
    async def insert_one(self,d):self.docs.append(dict(d));return SimpleNamespace(inserted_id=1)
class Base(dict):
    def __getitem__(self,name):
        if name not in self:self[name]=Col()
        return dict.__getitem__(self,name)

calls=[]
class FakeResponse:
    def __init__(self,status=202):self.status_code=status
class FakeClient:
    async def __aenter__(self):return self
    async def __aexit__(self,*args):return False
    async def post(self,url,headers=None,json=None):
        assert url=='https://correo.test/enviar'
        assert headers.get('Authorization')=='Bearer token-sintetico'
        assert json.get('to')=='ficticio@example.test'
        calls.append(json)
        return FakeResponse()

async def main():
    backup={k:os.environ.get(k) for k in ['EMAIL_API_URL','EMAIL_API_KEY','EMAIL_DEMO_MODE']}
    orig=notifications.httpx.AsyncClient
    try:
        os.environ.pop('EMAIL_API_URL',None);os.environ.pop('EMAIL_API_KEY',None)
        os.environ['EMAIL_DEMO_MODE']='1'
        base=Base()
        respuesta=await notifications.enviar_notificacion(base,'registro','ficticio@example.test','Código','Código 123456','op-12345678','123456')
        assert respuesta['estado']=='registrado_demo_sin_entrega'
        assert base['notifications'].docs[0]['codigo_demo']=='123456'
        os.environ['EMAIL_API_URL']='https://correo.test/enviar'
        os.environ['EMAIL_API_KEY']='token-sintetico'
        notifications.httpx.AsyncClient=lambda **kw:FakeClient()
        respuesta=await notifications.enviar_notificacion(base,'registro','ficticio@example.test','Código','Código 123456','op-12345678','123456')
        assert respuesta['estado']=='aceptado_por_api_entrega_no_confirmada'
        assert len(calls)==1
        assert 'codigo_demo' not in base['notifications'].docs[1]
        assert 'EMAIL_API_KEY' not in str(base['notifications'].docs[1])
        os.environ.pop('EMAIL_API_KEY')
        respuesta=await notifications.enviar_notificacion(base,'registro','ficticio@example.test','Código','Código 123456','op-12345678','123456')
        assert respuesta['estado']=='configuracion_incompleta_sin_entrega'
        print('Notificaciones aisladas: DEMO Mongo, REST HTTP aceptado simulado, configuración incompleta y ausencia de claves en registros OK.')
    finally:
        notifications.httpx.AsyncClient=orig
        for k,v in backup.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v

if __name__=='__main__':asyncio.run(main())
