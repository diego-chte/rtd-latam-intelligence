#!/usr/bin/env python3
"""
RTD México — ETL Pipeline
Transforms raw Datasur XLSX exports into structured JSON for the dashboard.

Usage:
    python etl.py --file1 FILE1.xlsx --file2 FILE2.xlsx --output data.json

Author: Zubral Intelligence
Date: 2026
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("ERROR: pandas not installed. Run: pip install pandas openpyxl")
    sys.exit(1)


# ─────────────────────────────────────────
# PRODUCT NORMALIZATION
# ─────────────────────────────────────────

def clean_producto(p: str) -> str:
    """Normalize product names to collapse duplicate descriptions."""
    p = str(p).upper().strip()
    if 'APEROL' in p: return 'APERITIVO APEROL'
    if 'SANGRIA KIRKLAND' in p: return 'SANGRIA KIRKLAND'
    if 'MIMOSA KIRKLAND' in p: return 'MIMOSA KIRKLAND'
    if 'JINRO' in p: return 'BEBIDA JINRO (SOJU)'
    if 'PREPARACION FERMENTADA' in p and 'MANZANA' in p: return 'FERMENTADA DE MANZANA'
    if 'BEBIDA ALCOHOLICA NATURAL A BASE DE MALTA' in p: return 'BEBIDA BASE MALTA'
    if 'SANGRIA' in p: return 'SANGRIA'
    if 'TEQUILA' in p: return 'TEQUILA'
    if 'SAKE' in p or 'VINO DE ARROZ' in p: return 'SAKE / VINO ARROZ'
    if 'SIDRA' in p: return 'SIDRA'
    if 'CHIVAS' in p: return 'WHISKY CHIVAS REGAL'
    if 'STELLA ROSA' in p: return 'BEBIDA STELLA ROSA'
    if 'VERDI' in p: return 'FERMENTADA ESPUMOSA VERDI'
    if 'MOSCATO' in p: return 'MOSCATO'
    if 'APERITIVO' in p: return 'APERITIVO (OTROS)'
    if 'ALCOHOL ETILICO' in p: return 'ALCOHOL ETILICO'
    if 'AGUARDIENTE' in p: return 'AGUARDIENTE'
    return p[:50]


def get_categoria(partida: int) -> str:
    p = str(partida)
    if p.startswith('2206'): return 'Fermentadas (22.06)'
    if p.startswith('2208'): return 'Destilados (22.08)'
    return 'Otros'


def get_tipo_producto(partida: int) -> str:
    mapping = {
        '22060091': 'Bebidas Fermentadas - Otras',
        '22060002': 'Bebidas Fermentadas - Mezclas',
        '22060001': 'Bebidas Refrescantes Base Limón',
        '22089003': 'Tequila',
        '22089001': 'Alcohol Etílico',
        '22089005': 'Mezcal',
        '22089007': 'Raicilla',
        '22089099': 'Destilados - Los Demás',
    }
    return mapping.get(str(partida), 'Otros')


# ─────────────────────────────────────────
# CORE ETL
# ─────────────────────────────────────────

def load_datasur(path: Path) -> pd.DataFrame:
    """Load a Datasur XLSX export into a clean DataFrame."""
    df = pd.read_excel(path, sheet_name='Datasur', header=0)
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    """Apply all transformations to raw Datasur data."""
    df = df.copy()

    # Fix year to 4-digit
    df['AÑO_FULL'] = df['AÑO'].apply(lambda x: 2000 + x if x < 100 else x)
    df['FECHA'] = df['AÑO_FULL'].astype(str) + '-' + df['MES'].astype(str).str.zfill(2)

    # Derived fields
    df['CATEGORIA'] = df['PARTIDA ARANCELARIA'].apply(get_categoria)
    df['TIPO_PRODUCTO'] = df['PARTIDA ARANCELARIA'].apply(get_tipo_producto)
    df['PRODUCTO_CLEAN'] = df['PRODUCTO'].apply(clean_producto)

    return df


def build_output(df: pd.DataFrame) -> dict:
    """Aggregate into all output layers for the dashboard."""

    # ── Summary KPIs ──
    total_fob = round(df['FOB USD'].sum(), 2)
    fob_fermentadas = round(df[df['CATEGORIA'] == 'Fermentadas (22.06)']['FOB USD'].sum(), 2)
    fob_destilados = round(df[df['CATEGORIA'] == 'Destilados (22.08)']['FOB USD'].sum(), 2)

    meta = {
        'total_fob_usd': total_fob,
        'total_ops': int(len(df)),
        'n_paises': int(df['PAÍS DE ORIGEN'].nunique()),
        'n_importadores': int(df['IMPORTADOR'].nunique()),
        'periodo': '2022-01 / 2026-04',
        'fob_fermentadas': fob_fermentadas,
        'fob_destilados': fob_destilados,
        'pct_fermentadas': round(fob_fermentadas / total_fob * 100, 1) if total_fob else 0,
        'pct_destilados': round(fob_destilados / total_fob * 100, 1) if total_fob else 0,
    }

    # ── Monthly trend ──
    monthly = df.groupby(['AÑO_FULL', 'MES', 'CATEGORIA']).agg(
        fob_usd=('FOB USD', 'sum'),
        ops=('NRO DOCUMENTO', 'count'),
        peso_kg=('PESO TOTAL DECLARACIÓN', 'sum')
    ).reset_index()
    monthly['fecha'] = monthly['AÑO_FULL'].astype(str) + '-' + monthly['MES'].astype(str).str.zfill(2)

    # ── Annual ──
    annual = df.groupby(['AÑO_FULL', 'CATEGORIA']).agg(
        fob_usd=('FOB USD', 'sum'),
        ops=('NRO DOCUMENTO', 'count'),
        n_paises=('PAÍS DE ORIGEN', 'nunique'),
        n_importadores=('IMPORTADOR', 'nunique')
    ).reset_index()

    # ── Annual pivot (for YoY) ──
    annual_pivot = df.groupby('AÑO_FULL')['FOB USD'].sum().reset_index()
    annual_pivot['yoy_pct'] = annual_pivot['FOB USD'].pct_change() * 100
    annual_pivot = annual_pivot.round(2)

    # ── Country totals ──
    country_total = df.groupby('PAÍS DE ORIGEN').agg(
        fob_usd=('FOB USD', 'sum'),
        ops=('NRO DOCUMENTO', 'count')
    ).reset_index().sort_values('fob_usd', ascending=False).head(20)

    # ── Country by category ──
    country_cat = df.groupby(['PAÍS DE ORIGEN', 'CATEGORIA']).agg(
        fob_usd=('FOB USD', 'sum'),
        ops=('NRO DOCUMENTO', 'count')
    ).reset_index().sort_values('fob_usd', ascending=False).head(30)

    # ── Importers ──
    importer = df.groupby(['IMPORTADOR', 'ESTADO DEL IMPORTADOR', 'CIUDAD DEL IMPORTADOR']).agg(
        fob_usd=('FOB USD', 'sum'),
        ops=('NRO DOCUMENTO', 'count'),
        n_paises=('PAÍS DE ORIGEN', 'nunique')
    ).reset_index().sort_values('fob_usd', ascending=False).head(20)

    # ── Products ──
    product = df.groupby(['PRODUCTO_CLEAN', 'CATEGORIA']).agg(
        fob_usd=('FOB USD', 'sum'),
        ops=('NRO DOCUMENTO', 'count')
    ).reset_index().sort_values('fob_usd', ascending=False).head(20)

    # ── Aduana ──
    aduana = df.groupby('ADUANA, ESTADO, PUERTO').agg(
        fob_usd=('FOB USD', 'sum'),
        ops=('NRO DOCUMENTO', 'count')
    ).reset_index().sort_values('fob_usd', ascending=False).head(10)

    # ── Estado ──
    estado = df.groupby('ESTADO DEL IMPORTADOR').agg(
        fob_usd=('FOB USD', 'sum'),
        ops=('NRO DOCUMENTO', 'count')
    ).reset_index().sort_values('fob_usd', ascending=False).head(10)

    # ── Fact table ──
    fact_cols = [
        'AÑO_FULL', 'MES', 'FECHA', 'CATEGORIA', 'TIPO_PRODUCTO', 'PRODUCTO_CLEAN',
        'IMPORTADOR', 'ESTADO DEL IMPORTADOR', 'ADUANA, ESTADO, PUERTO',
        'PAÍS DE ORIGEN', 'NOMBRE PROVEEDOR', 'FOB USD', 'FOB MXN',
        'TASA DE CAMBIO', 'CANTIDAD ESTADÍSTICA', 'NRO DOCUMENTO'
    ]
    fact = df[fact_cols].copy()
    fact.columns = [
        'anio', 'mes', 'fecha', 'categoria', 'tipo_producto', 'producto',
        'importador', 'estado', 'aduana', 'pais_origen', 'proveedor',
        'fob_usd', 'fob_mxn', 'tasa_cambio', 'cantidad_litros', 'nro_doc'
    ]

    return {
        'meta': meta,
        'monthly': monthly.to_dict(orient='records'),
        'annual': annual.to_dict(orient='records'),
        'annual_pivot': annual_pivot.to_dict(orient='records'),
        'country_total': country_total.to_dict(orient='records'),
        'country_cat': country_cat.to_dict(orient='records'),
        'importer': importer.to_dict(orient='records'),
        'product': product.to_dict(orient='records'),
        'aduana': aduana.to_dict(orient='records'),
        'estado': estado.to_dict(orient='records'),
        'facts': fact.to_dict(orient='records'),
    }


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='RTD México — ETL Pipeline')
    parser.add_argument('--file1', required=True, help='Primary Datasur XLSX (e.g. 22.06 + 22.08 complete)')
    parser.add_argument('--file2', default=None, help='Secondary Datasur XLSX (optional, 22.08 subset — not added to avoid double-counting)')
    parser.add_argument('--output', default='data.json', help='Output JSON path')
    args = parser.parse_args()

    print(f'[ETL] Loading {args.file1}...')
    df = load_datasur(Path(args.file1))
    print(f'[ETL] Loaded {len(df)} rows, {df["PARTIDA ARANCELARIA"].nunique()} partidas')

    if args.file2:
        print(f'[ETL] Note: File2 ({args.file2}) provided. File1 already includes all 2208 rows — File2 not merged to avoid double counting.')

    print('[ETL] Transforming...')
    df = transform(df)

    print('[ETL] Aggregating layers...')
    output = build_output(df)

    out_path = Path(args.output)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, default=str)

    size_kb = out_path.stat().st_size // 1024
    print(f'[ETL] Done! → {out_path} ({size_kb} KB)')
    print(f'      Total FOB: ${output["meta"]["total_fob_usd"]:,.0f}')
    print(f'      Registros: {output["meta"]["total_ops"]}')
    print(f'      Países: {output["meta"]["n_paises"]}')
    print(f'      Importadores: {output["meta"]["n_importadores"]}')


if __name__ == '__main__':
    main()
