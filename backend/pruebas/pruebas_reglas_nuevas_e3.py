"""Pruebas de contrato aisladas de E3. No representan pruebas E2E con servicios reales."""
import asyncio
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import httpx

ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(ROOT))
from backend.domain.delivery import distancia_km, verificar_cobertura

os.environ.setdefault('VAULT_TOKEN', 'token-de-prueba-no-real')
spec=importlib.util.spec_from_file_location('gateway_contratos', ROOT/'backend/api-gateway/gateway.py')
gateway=importlib.util.module_from_spec(spec)
spec.loader.exec_module(gateway)


def test_delivery():
    assert distancia_km(0, 0, 0, 0) == 0
    dentro, d=verificar_cobertura(-33.51,-70.75,-33.51,-70.75,3)
    assert dentro and d==0
    dentro, d=verificar_cobertura(-33.53,-70.75,-33.51,-70.75,3)
    assert dentro and 2 < d < 3
    dentro, d=verificar_cobertura(-33.55,-70.75,-33.51,-70.75,3)
    assert not dentro and d > 3
    try: verificar_cobertura(0, 0, None, None)
    except ValueError: pass
    else: raise AssertionError('Sin coordenadas debe fallar cerrado')


class FakeResponse:
    def __init__(self,code,obj):
        self.status_code=code; self.obj=obj; self.content=json.dumps(obj).encode()
    def json(self):return self.obj


class FakeClient:
    def __init__(self,actions,fail_clients=False):
        self.actions=actions;self.fail_clients=fail_clients
    async def __aenter__(self):return self
    async def __aexit__(self,*a):return False
    async def get(self,url,headers=None,params=None):
        self.actions.append(('GET',url))
        assert '/v1/secret/data/gateway' in url
        return FakeResponse(200, {'data':{'data':{'auth_introspection_secret':'falso-auth','backend_shared_secret':'falso-backend','graphql_shared_secret':'falso-graphql'}}})
    async def post(self,url,headers=None,json=None,content=None):
        self.actions.append(('POST',url))
        if '/register' in url:
            assert 'username' in json and 'password' in json
            assert headers['X-Gateway-Auth-Secret']=='falso-auth'
            return FakeResponse(201,{'user_id':'USR-999999999','username':json['username']})
        if '/email/send-code' in url:
            return FakeResponse(200,{'estado':'registrado_demo_sin_entrega','modo':'demo','codigo_demo':'123456'})
        if '/clients' in url:
            assert 'password' not in json and json['id']=='USR-999999999'
            assert headers['X-Gateway-Secret']=='falso-backend'
            return FakeResponse(409 if self.fail_clients else 201, {'detail':'Duplicado' if self.fail_clients else 'Registrado'})
        raise AssertionError(url)
    async def delete(self,url,headers=None):
        self.actions.append(('DELETE',url))
        assert '/internal/registration/USR-999999999' in url
        assert headers['X-Gateway-Auth-Secret']=='falso-auth'
        return FakeResponse(200,{'rollback':True})


async def test_registro():
    payload={
        'username':'usuario_demo_999','password':'fake-password-123',
        'run':'FICTICIO-999','nombre':'Ejemplo Usuario',
        'direccion':'Calle Ficticia 100','comuna':'Maipú','provincia':'Santiago',
        'region':'Metropolitana','fecha_nacimiento':'1995-01-01',
        'sexo':'X','correo':'demo999@example.test','telefono':'000000000'
    }
    original=gateway.httpx
    try:
        for fail,expected in [(False,201),(True,409)]:
            actions=[]
            gateway.httpx=SimpleNamespace(
                AsyncClient=lambda **kwargs: FakeClient(actions,fail_clients=fail),
                RequestError=httpx.RequestError)
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=gateway.app),base_url='http://local') as client:
                r=await client.post('/api/auth/register',json=payload)
                assert r.status_code==expected,(r.status_code,r.text)
                assert any('/register' in path for _,path in actions)
                assert any('/clients' in path for _,path in actions)
                assert any(verb=='DELETE' for verb,_ in actions)==fail
                assert r.headers.get('X-Operacion')
    finally:gateway.httpx=original


def test_roles():
    assert gateway.destino_autorizado('PUT','orders/ORD-ABC/status',['staff'])==gateway.ORDERS_URL
    assert gateway.destino_autorizado('PUT','orders/ORD-ABC/status',['user']) is None
    assert gateway.destino_autorizado('POST','orders/ORD-ABC/cancel',['staff']) is None
    assert gateway.destino_autorizado('POST','orders/ORD-ABC/cancel',['user'])==gateway.ORDERS_URL
    assert gateway.destino_autorizado('POST','payments/PAY-ABC/test-confirm',['user']) is None
    assert gateway.destino_autorizado('GET','orders/ORD-ABC/comprobante',['user'])==gateway.ORDERS_URL
    assert gateway.destino_autorizado('GET','orders/eventos',['admin'])==gateway.ORDERS_URL
    assert gateway.destino_autorizado('GET','orders/eventos',['staff']) is None


if __name__=='__main__':
    test_delivery();test_roles();asyncio.run(test_registro())
    print('8 assertions groups: cobertura 3 km, registro exitoso/reversión, permisos por rol y trazabilidad OK (mocks aislados).')
