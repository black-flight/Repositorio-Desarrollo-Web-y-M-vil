"""Genera .env local desde .env.example; no escribe secretos en Git."""
from pathlib import Path
import secrets
import sys

root=Path(__file__).resolve().parents[2]
filename=root/'.env'
if filename.exists():
    print('Ya existe .env. No se sobrescribe para proteger claves previas.')
    sys.exit(0)
lines=[]
for line in (root/'.env.example').read_text(encoding='utf-8').splitlines():
    if not line or line.startswith('#') or '=' not in line:
        lines.append(line)
        continue
    key, value=line.split('=',1)
    if value == 'GENERAR_LOCAL':
        value=secrets.token_urlsafe(24)
    lines.append(key+'='+value)
# Vault usa el mismo token en el contenedor de desarrollo y en el cliente Vault.
root_token=next(x.split('=',1)[1] for x in lines if x.startswith('VAULT_DEV_ROOT_TOKEN_ID='))
lines=[('VAULT_TOKEN='+root_token) if x.startswith('VAULT_TOKEN=') else x for x in lines]
filename.write_text('\n'.join(lines)+'\n',encoding='utf-8')
try: filename.chmod(0o600)
except OSError: pass
print('.env creado con credenciales de prueba únicas. No lo subas a GitHub ni lo muestres en el video.')
print('Coordenadas de la sucursal: SINTÉTICAS para prueba. Sustituir para operar con tienda real.')
