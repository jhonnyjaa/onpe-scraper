import requests
import json
import pandas as pd
from datetime import datetime, timezone
import os
import sys
import base64

BASE_URL = "https://resultadoelectoral.onpe.gob.pe/presentacion-backend/resumen-general"
PARAMS = {"idEleccion": 10, "tipoFiltro": "eleccion"}

os.makedirs("data/snapshots", exist_ok=True)
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
ts_epoch  = datetime.now(timezone.utc).isoformat()

# Sesion simulando navegador real
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

# Guardar archivos localmente
snapshot_totales_path     = f"data/snapshots/{timestamp}_totales.json"
snapshot_part_path        = f"data/snapshots/{timestamp}_participantes.json"
totales_csv               = "data/historico_totales.csv"
part_csv                  = "data/historico_participantes.csv"

with open(snapshot_totales_path, "w", encoding="utf-8") as f:
    json.dump({"captured_at": ts_epoch, "payload": totales}, f, ensure_ascii=False, indent=2)

with open(snapshot_part_path, "w", encoding="utf-8") as f:
    json.dump({"captured_at": ts_epoch, "payload": participantes}, f, ensure_ascii=False, indent=2)

# Historico totales
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

# ── Subir archivos a GitHub via API ──────────────────────────────────────────
token       = os.environ.get("GITHUB_TOKEN")
github_user = os.environ.get("GITHUB_USER", "jhonnyjaa")
repo_name   = os.environ.get("GITHUB_REPO", "onpe-scraper")

if not token:
    print("⚠️ GITHUB_TOKEN no encontrado, saltando push")
    sys.exit(0)

github_api = requests.Session()
github_api.headers.update({
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
})

def github_upload(local_path, repo_path):
    """Sube un archivo local a GitHub via API."""
    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    url = f"https://api.github.com/repos/{github_user}/{repo_name}/contents/{repo_path}"

    # Verificar si el archivo ya existe (para obtener su SHA)
    r = github_api.get(url)
    sha = r.json().get("sha") if r.status_code == 200 else None

    payload = {
        "message": f"snapshot {timestamp} - {repo_path}",
        "content": content_b64,
    }
    if sha:
        payload["sha"] = sha

    r = github_api.put(url, json=payload)
    if r.status_code in (200, 201):
        print(f"✅ Subido: {repo_path}")
    else:
        print(f"❌ Error subiendo {repo_path}: {r.status_code} {r.text[:200]}")

print("Subiendo archivos a GitHub...")
github_upload(snapshot_totales_path, snapshot_totales_path)
github_upload(snapshot_part_path,    snapshot_part_path)
github_upload(totales_csv,           totales_csv)
github_upload(part_csv,              part_csv)

print("🎉 Todo listo!")