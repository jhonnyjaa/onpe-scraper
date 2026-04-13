import requests
import json
import pandas as pd
from datetime import datetime, timezone
import os
import sys

BASE_URL = "https://resultadoelectoral.onpe.gob.pe/presentacion-backend/resumen-general"
PARAMS = {"idEleccion": 10, "tipoFiltro": "eleccion"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-PE,es;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://resultadoelectoral.onpe.gob.pe",
    "Referer": "https://resultadoelectoral.onpe.gob.pe/",
    "Connection": "keep-alive",
}

os.makedirs("data/snapshots", exist_ok=True)

timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%SZ")
ts_epoch  = datetime.now(timezone.utc).isoformat()

def fetch(endpoint):
    url = f"{BASE_URL}/{endpoint}"
    r = requests.get(url, params=PARAMS, headers=HEADERS, timeout=15)
    print(f"[{endpoint}] status={r.status_code} size={len(r.content)} bytes")
    if not r.content:
        print(f"ERROR: respuesta vacia en {endpoint}")
        print(f"Response headers: {dict(r.headers)}")
        sys.exit(1)
    try:
        return r.json()
    except Exception as e:
        print(f"ERROR parseando JSON: {e}")
        print(f"Contenido crudo: {r.text[:500]}")
        sys.exit(1)

totales       = fetch("totales")
participantes = fetch("participantes")

with open(f"data/snapshots/{timestamp}_totales.json", "w", encoding="utf-8") as f:
    json.dump({"captured_at": ts_epoch, "payload": totales}, f, ensure_ascii=False, indent=2)

with open(f"data/snapshots/{timestamp}_participantes.json", "w", encoding="utf-8") as f:
    json.dump({"captured_at": ts_epoch, "payload": participantes}, f, ensure_ascii=False, indent=2)

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
print(f"   Actas contabilizadas: {t.get('actasContabilizadas')*100:.2f}%")
print(f"   Total votos validos:  {t.get('totalVotosValidos'):,}")