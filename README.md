# RTD LATAM — Inteligencia de Mercado & México Aduanal

Dashboard ejecutivo interactivo de inteligencia de mercado para bebidas Ready to Drink (RTD) en Latinoamérica, con análisis profundo del mercado mexicano basado en datos aduanales Datasur 2022–2026.

---

## 🗂 Estructura del Repositorio

```
rtd-latam-intelligence/
│
├── index.html                  ← Dashboard principal (single-file, sin build)
│
├── data/
│   └── mexico_aduana.json      ← Datos ETL procesados (generado por etl/etl_mexico.py)
│
├── etl/
│   └── etl_mexico.py           ← Pipeline ETL Python para Datasur XLSX
│
├── assets/                     ← (Vacío — espacio para logos, iconos, etc.)
│
├── .gitignore
└── README.md
```

> **Nota:** Los archivos `.xlsx` fuente de Datasur **no se incluyen en el repositorio** (`.gitignore`). El `data/mexico_aduana.json` es el resultado del ETL ya procesado y sí se versiona.

---

## 🚀 Cómo Usar

### 1. Clonar el repositorio

```bash
git clone https://github.com/diego-chte/rtd-latam-intelligence.git
cd rtd-latam-intelligence
```

### 2. Abrir el dashboard

El dashboard es un HTML estático que carga el JSON por `fetch()`, por lo que necesita un servidor HTTP local:

```bash
# Python (más simple)
python -m http.server 8080

# Node.js
npx serve .

# VS Code → instala "Live Server" → clic derecho en index.html → "Open with Live Server"
```

Luego abre: **http://localhost:8080**

### 3. Actualizar datos (cuando tengas nuevos XLSX de Datasur)

```bash
# Instalar dependencias Python
pip install pandas openpyxl

# Ejecutar ETL
python etl/etl_mexico.py \
  --file1 /ruta/a/datasur_completo.xlsx \
  --output data/mexico_aduana.json

# El dashboard se actualiza automáticamente al recargar el navegador
```

---

## 📊 Estructura del Dashboard — 10 Vistas

### SECCIÓN A — Investigación RTD LATAM
Basada en el informe de mercado (IWSR, Euromonitor, Market.us, Future Market Insights)

| # | Vista | Contenido |
|---|---|---|
| 01 | **Vista General** | Tesis de mercado, proyección global, mix por base de formulación, CAGR regional |
| 02 | **Mercados & CAGR** | Scorecard interactivo por país, perfil detallado, proyecciones de valor |
| 03 | **Competidores** | Mapa precio vs ABV, fichas de marca, matriz competitiva completa |
| 04 | **Estructura Fiscal** | Comparativa de carga impositiva por país, alertas y casos especiales |
| 05 | **Consumidor & Tendencias** | Perfil demográfico, frecuencia, sabores emergentes, atributos por generación |

### SECCIÓN B — México Aduanal
Basada en datos transaccionales Datasur (partidas 22.06 + 22.08)

| # | Vista | Contenido |
|---|---|---|
| 06 | **MX · Vista General** | KPIs, tendencia mensual, top países/importadores/productos |
| 07 | **MX · Tendencia** | Línea de tiempo completa ene 2022–abr 2026, YoY, tabla mensual |
| 08 | **MX · Origen & Aduana** | Top 15 países, puertos de entrada, distribución por estado importador |
| 09 | **MX · Actores** | Ranking importadores, concentración de mercado, directorio buscable |
| 10 | **MX · Explorador** | Drill-down fila a fila con 4 filtros combinados, 3,643 registros |

---

## 📐 Modelo de Datos

### A — Datos de Investigación (hardcoded en index.html)

```javascript
COMPETITORS[]       // 9 marcas con precio, ABV, base, packaging
MARKETS[]           // 6 países con CAGR, perfil, notas estratégicas
TAXES[]             // 9 registros fiscales (HS code, arancel, impuesto especial, IVA)
```

### B — Mexico Aduana JSON (`data/mexico_aduana.json`)

```json
{
  "meta":          // KPIs globales: total FOB, operaciones, países, período
  "monthly":       // Tendencia mensual por categoría (22.06 / 22.08)
  "annual":        // Totales anuales por categoría
  "annual_pivot":  // YoY growth por año
  "country_total": // Top 20 países por FOB USD
  "country_cat":   // Top 30 combinaciones país × categoría
  "importer":      // Top 20 importadores por FOB
  "product":       // Top 20 productos normalizados por FOB
  "aduana":        // Top 10 puertos / aduanas por FOB
  "estado":        // Top 10 estados del importador
  "facts":         // Tabla de hechos completa — 3,643 filas
}
```

### Partidas Arancelarias Cubiertas

| Partida | Descripción | Registros |
|---|---|---|
| 22060091 | Bebidas fermentadas otras (sake, sangría, sidra…) | 2,242 |
| 22089099 | Destilados los demás (aperitivos, licores, RTD) | 772 |
| 22060002 | Mezclas de bebidas fermentadas | 513 |
| 22089003 | Tequila | 83 |
| 22089001 | Alcohol etílico sin desnaturalizar | 32 |
| 22089005 | Mezcal | 1 |

---

## 📈 Hallazgos Clave

### Mercado Global RTD
- Valor proyectado 2034: **USD 42.9B** (CAGR 5.9%)
- RTD Cocktails: **USD 9.44B** en 2036 (CAGR 13.7%)
- Destilados dominan: **47.8% del share** global por valor
- Consumidores frecuentes (≥1/semana): **55%** en 2025 vs 39% en 2022

### México Aduanal
- Total FOB 2022–2026: **USD 53.7M** (73.7% fermentadas, 26.3% destilados)
- Crecimiento 2024 vs 2023: **+96.5%** en valor FOB
- País dominante: **Italia** (33.7%) — principalmente Aperol/Campari
- Importador líder: **Importadora Primex** (~$18.4M — Sangría Kirkland)
- Concentración: **Top 3 = 51%** del valor total
- Puerto principal: **Veracruz** (58.6% del FOB total)

---

## 🏗 Tecnologías

| Componente | Tecnología |
|---|---|
| Dashboard | HTML5 + JavaScript vanilla (sin framework, sin build) |
| Visualizaciones | Chart.js 4.4.1 (CDN) |
| ETL | Python 3.x · pandas · openpyxl |
| Datos | JSON estático (no requiere backend ni base de datos) |
| Deploy | GitHub Pages, Netlify, o cualquier servidor estático |

---

## 🌐 Deploy en GitHub Pages

```bash
# En el repositorio de GitHub:
# Settings → Pages → Source: Deploy from branch → main → / (root) → Save
```

El dashboard estará disponible en: `https://diego-chte.github.io/rtd-latam-intelligence/`

---

## 📁 Cómo Agregar al Repo Existente (diego-chte)

```bash
# Si ya tienes el repo clonado:
cd tu-repo-existente

# Copiar los archivos nuevos
cp /ruta/index.html .
mkdir -p data etl
cp /ruta/data/mexico_aduana.json data/
cp /ruta/etl/etl_mexico.py etl/

# Commit
git add .
git commit -m "Add RTD LATAM dashboard v2 - research + Mexico aduana"
git push
```

---

*Datos: Datasur MX · Período: Ene 2022 – Abr 2026 · Partidas NANDINA 22.06 + 22.08*  
*Investigación: IWSR · Market.us · Euromonitor · Future Market Insights · StrategyHelix*
