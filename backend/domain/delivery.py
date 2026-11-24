"""Distancia local aproximada en línea recta; no representa kilómetros viales."""
from math import cos, radians, sqrt, isfinite

def validar_coordenada(lat, lon):
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not isfinite(v) for v in (lat, lon)):
        raise ValueError("Coordenadas numéricas finitas requeridas")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("Coordenadas fuera de rango")

def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Aproximación equirectangular válida para trayectos locales cercanos a la tienda."""
    validar_coordenada(lat1, lon1)
    validar_coordenada(lat2, lon2)
    delta_lon = ((lon2 - lon1 + 180) % 360) - 180
    km_lat = (lat2 - lat1) * 111.2
    km_lon = delta_lon * 111.2 * cos(radians(lat1))
    return sqrt(km_lat ** 2 + km_lon ** 2)

def verificar_cobertura(lat_cliente, lon_cliente, lat_tienda, lon_tienda, radio=3.0):
    if lat_tienda is None or lon_tienda is None:
        raise ValueError("Coordenadas de sucursal no configuradas")
    if isinstance(radio, bool) or not isinstance(radio, (float, int)) or not isfinite(radio) or radio <= 0:
        raise ValueError("Radio inválido")
    distancia = distancia_km(lat_tienda, lon_tienda, lat_cliente, lon_cliente)
    # El rechazo usa el valor sin redondear para evitar falsos positivos en el límite.
    return distancia <= radio, round(distancia, 3)
