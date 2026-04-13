# 🗳️ ONPE Electoral Scraper — Elecciones Perú 2026

Captura automática de resultados electorales en tiempo real desde la API oficial de la ONPE, cada 5 minutos, con almacenamiento histórico para análisis y auditoría ciudadana.

## ¿Qué hace este proyecto?

Cada 5 minutos un job automatizado consulta la API oficial de la ONPE y guarda un snapshot completo de los resultados. Esto permite:

- Tener un registro histórico e inmutable de cómo evolucionaron los votos
- Detectar anomalías como saltos bruscos o cambios de tendencia
- Analizar la velocidad de conteo de actas por intervalo de tiempo
- Servir como evidencia de auditoría ciudadana independiente

## Estructura del repo
```bash
onpe-scraper/
├── scraper.py                     # Script principal
├── requirements.txt               # Dependencias Python
├── railway.toml                   
└── data/
    ├── historico_totales.csv      # Serie temporal del avance del conteo
    ├── historico_participantes.csv # Votos por partido a lo largo del tiempo
    └── snapshots/
        └── TIMESTAMP_*.json       # Respuesta cruda de ONPE con timestamp
```

## Archivos de datos

### `historico_totales.csv`
Registra el avance general del conteo en cada captura.

| Columna | Descripción |
|---|---|
| `captured_at` | Timestamp UTC del momento de captura |
| `fechaActualizacion` | Timestamp de la última actualización en ONPE |
| `actasContabilizadas_pct` | Porcentaje de actas contabilizadas |
| `contabilizadas` | Número de actas contabilizadas |
| `totalActas` | Total de actas a nivel nacional |
| `totalVotosEmitidos` | Total de votos emitidos |
| `totalVotosValidos` | Total de votos válidos |
| `participacionCiudadana` | Porcentaje de participación ciudadana |

### `historico_participantes.csv`
Registra los votos por partido/candidato en cada captura.

| Columna | Descripción |
|---|---|
| `captured_at` | Timestamp UTC del momento de captura |
| `codigoAgrupacion` | Código interno del partido |
| `nombreAgrupacion` | Nombre del partido político |
| `nombreCandidato` | Nombre completo del candidato |
| `totalVotosValidos` | Votos válidos acumulados |
| `porcentajeVotosValidos` | Porcentaje sobre votos válidos |
| `porcentajeVotosEmitidos` | Porcentaje sobre votos emitidos |

### `snapshots/`
Respuestas JSON crudas de la API de ONPE con timestamp de captura. Son la fuente de verdad — si hubiera cualquier discrepancia con los CSVs, estos archivos permiten reconstruir todo desde cero.


## Fuente de datos

API oficial de la ONPE: [resultadoelectoral.onpe.gob.pe](https://resultadoelectoral.onpe.gob.pe)

Los datos son públicos y provienen directamente del sistema oficial de cómputo electoral del Perú. Este proyecto no modifica ni interpreta los datos — solo los captura y almacena con timestamp.

## Infraestructura

- **Railway** — ejecuta el scraper cada 5 minutos
- **GitHub** — almacena los datos con historial inmutable de commits como garantía de integridad

## Licencia

MIT — libre para usar, compartir y modificar con atribución.