"""Pruebas de reglas de puro Python y contratos disponibles sin MongoDB/Docker.
NO equivale a comprobar persistencia ni a consumir un mensaje ActiveMQ real.
"""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from backend.domain.delivery import distancia_km, verificar_cobertura

class CoberturaTest(unittest.TestCase):
    def test_distancia_cero(self):
        self.assertEqual(distancia_km(-33.51,-70.75,-33.51,-70.75),0)

    def test_dentro_y_fuera_3km(self):
        self.assertTrue(verificar_cobertura(-33.52,-70.75,-33.51,-70.75)[0])
        self.assertFalse(verificar_cobertura(-33.55,-70.75,-33.51,-70.75)[0])

    def test_borde_sin_redondear(self):
        # 3 km / 111.2 km por grado en la misma longitud.
        limite=-33.51+(3.0/111.2)
        self.assertTrue(verificar_cobertura(limite,-70.75,-33.51,-70.75)[0])
        self.assertFalse(verificar_cobertura(limite+0.000001,-70.75,-33.51,-70.75)[0])

    def test_invalidas(self):
        for l in (float('nan'), float('inf'), 95):
            with self.assertRaises(ValueError):distancia_km(l,-70,0,0)
        with self.assertRaises(ValueError):verificar_cobertura(0,0,None,None)

class ContratosTest(unittest.TestCase):
    def test_json_modelo_codigo_compra(self):
        from pydantic import BaseModel,Field,ValidationError
        class Compra(BaseModel):
            codigo_compra: str=Field(pattern=r'^[A-Za-z0-9._:-]{16,128}$')
        self.assertEqual(Compra(codigo_compra='x'*16).codigo_compra,'x'*16)
        with self.assertRaises(ValidationError):Compra(codigo_compra='ABC')

if __name__=='__main__':unittest.main(verbosity=2)
