import requests
import json
import pandas as pd
from datetime import datetime, timezone
import os
import sys
import subprocess

BASE_URL = "https://resultadoelectoral.onpe.gob.pe/presentacion-backend/resumen-general"
PARAMS = {"idEleccion": 10, "tipoFiltro": "eleccion"}

os.makedirs("data/snapshots", exist_ok=True)
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
ts_epoch  = datetime.now(timezone.utc).isoformat()

# Sesion simulando navegador
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-PE,es;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://resultadoelectoral.onpe.gob.pe/",
    "Origin": "https://resultadoelectoral.onpe.gob.pe",
    "Connection": "keep-alive",
})

# Visitar pagina principal para obtener cookies
print("Iniciando sesion en ONPE...")
home = session.get("https://resultadoelectoral.onpe.gob.pe/", timeout=15)
print(f"Home status: {home.status_code}")

def fetch(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    r = session.get(url, params=PARAMS, timeout=15)
    print(f"[{endpoint}] status={r.status_code} size={len(r.content)} bytes")
    if r.content[:1] == b'<':
        print(f"ERROR: devolvio HTML en vez de JSON")
        print(f"Primeros 300 chars: {r.text[:300]}")
        sys.exit(1)
    try:
        return r.json()
    except Exception as e:
        print(f"ERROR parseando JSON: {e}")
        print(f"Contenido crudo: {r.text[:500]}")
        sys.exit(1)

# Fetch datos
totales       = fetch("totales")
participantes = fetch("participantes")

# Snapshots crudos
with open(f"data/snapshots/{timestamp}_totales.json", "w", encoding="utf-8") as f:
    json.dump({"captured_at": ts_epoch, "payload": totales}, f, ensure_ascii=False, indent=2)

with open(f"data/snapshots/{timestamp}_participantes.json", "w", encoding="utf-8") as f:
    json.dump({"captured_at": ts_epoch, "payload": participantes}, f, ensure_ascii=False, indent=2)

# Historico totales
totales_csv = "data/historico_totales.csv"
t = totales["data"]
row_totales = {
    "captured_at":             ts_epoch,
    "fechaActualizacion":      t.get("fechaActualizacion"),
    "actasContabilizadas_pct": t.get("actasContabilizadas"),
    "contabilizadas":          t.get("contabilizadas"),
    "totalActas":              t.get("totalActas"),
    "pendientesJee":           t.get("pendientesJee"),
    "totalVotosEmitidos":      t.get("totalVotosEmitidos"),
    "totalVotosValidos":       t.get("totalVotosValidos"),
    "participacionCiudadana":  t.get("participacionCiudadana"),
}
df_t = pd.DataFrame([row_totales])
if os.path.exists(totales_csv):
    df_t.to_csv(totales_csv, mode="a", header=False, index=False)
else:
    df_t.to_csv(totales_csv, index=False)

# Historico participantes
part_csv = "data/historico_participantes.csv"
rows_part = []
for p in participantes["data"]:
    rows_part.append({
        "captured_at":             ts_epoch,
        "codigoAgrupacion":        p.get("codigoAgrupacionPolitica"),
        "nombreAgrupacion":        p.get("nombreAgrupacionPolitica"),
        "nombreCandidato":         p.get("nombreCandidato"),
        "dniCandidato":            p.get("dniCandidato"),
        "totalVotosValidos":       p.get("totalVotosValidos"),
        "porcentajeVotosValidos":  p.get("porcentajeVotosValidos"),
        "porcentajeVotosEmitidos": p.get("porcentajeVotosEmitidos"),
    })
df_p = pd.DataFrame(rows_part)
if os.path.exists(part_csv):
    df_p.to_csv(part_csv, mode="a", header=False, index=False)
else:
    df_p.to_csv(part_csv, index=False)

print(f"✅ Snapshot guardado: {timestamp}")
print(f"   Actas contabilizadas: {t.get('actasContabilizadas')}%")
print(f"   Total votos validos:  {t.get('totalVotosValidos'):,}")

# Push a GitHub
token = os.environ.get("GITHUB_TOKEN")
github_user = os.environ.get("GITHUB_USER", "jhonnyjaa")
repo_name   = os.environ.get("GITHUB_REPO", "onpe-scraper")

if token:
    print("Haciendo push a GitHub...")
    repo_url = f"https://{token}@github.com/{github_user}/{repo_name}.git"
    subprocess.run(["git", "config", "user.name", "railway-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "bot@railway.local"], check=True)
    subprocess.run(["git", "remote", "set-url", "origin", repo_url], check=True)
    subprocess.run(["git", "add", "data/"], check=True)
    result = subprocess.run(["git", "diff", "--staged", "--quiet"])
    if result.returncode != 0:
        subprocess.run(["git", "commit", "-m", f"snapshot {timestamp}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Push a GitHub exitoso")
    else:
        print("ℹ️ Sin cambios que commitear")
else:
    print("⚠️ GITHUB_TOKEN no encontrado, saltando push")