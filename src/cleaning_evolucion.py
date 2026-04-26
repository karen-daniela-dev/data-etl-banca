import pandas as pd
import numpy as np
import re
from collections import Counter

# ─────────────────────────────────────────
# 1. CARGA DE DATOS
# ─────────────────────────────────────────
def load_data(path: str) -> pd.DataFrame:
    """
    Carga el dataset con manejo básico de encoding.
    """
    try:
        df = pd.read_csv(path, sep="\t", encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, sep="\t", encoding="latin1")
    
    return df



def compute_producto_metrics(df: pd.DataFrame) -> dict:
    col = df["producto"]

    # Nulos
    null_real = col.isna().sum()
    null_fake = col.astype(str).str.strip().isin(["0", "NULL", ""]).sum()
    total_problemas = null_real + null_fake

    # Básicos
    total_registros = len(df)
    total_unicos = col.nunique()

    # Top
    top_values = col.value_counts().head(20)

    # Encoding
    encoding_pattern = r"[ÃÂ�]"
    encoding_issues = col[col.astype(str).str.contains(encoding_pattern, regex=True, na=False)]

    # Caracteres raros
    weird_pattern = r"[^a-zA-Z0-9\s_]"
    weird_values = col[col.astype(str).str.contains(weird_pattern, regex=True, na=False)]

    # Longitud
    lengths = col.astype(str).str.len().describe()

    # Tokens
    tokens = col.fillna("").astype(str).str.upper().str.split()
    all_tokens = [
        token
        for sublist in tokens
        if isinstance(sublist, list)
        for token in sublist
        if token
    ]

    from collections import Counter
    top_tokens = Counter(all_tokens).most_common(20)

    return {
        "total_registros": total_registros,
        "total_unicos": total_unicos,
        "null_real": null_real,
        "null_fake": null_fake,
        "total_problemas": total_problemas,
        "top_values": top_values,
        "encoding_issues": encoding_issues,
        "weird_values": weird_values,
        "lengths": lengths,
        "top_tokens": top_tokens
    }

def diagnose_producto(metrics: dict):
    print("\n" + "="*50)
    print("📊 DIAGNÓSTICO DE COLUMNA: producto")
    print("="*50)
    
    print(f"Total Registros: {metrics['total_registros']}")

    print("\n🔹 Valores nulos o sospechosos:")
    print(f"NaN: {metrics['null_real']}")
    print(f"0/NULL/vacíos: {metrics['null_fake']}")

    print("\n🔹 Número de valores únicos:")
    print(metrics["total_unicos"])

    print("\n🔹 Top 20 valores más frecuentes:")
    print(metrics["top_values"])

    print("\n🔹 Posibles problemas de encoding:")
    print(metrics["encoding_issues"].head(10))

    print("\n🔹 Strings con caracteres no alfabéticos relevantes:")
    print(metrics["weird_values"].head(10))

    print("\n🔹 Longitud de texto (distribución):")
    print(metrics["lengths"])

    print("\n🔹 Tokens más frecuentes:")
    print(metrics["top_tokens"])


def generate_report(metrics: dict, output_path="report_producto.txt"):
    with open(output_path, "w", encoding="utf-8") as f:

        f.write("📊 REPORTE DE CALIDAD DE DATOS - COLUMNA 'producto'\n")
        f.write("="*60 + "\n\n")

        # RESUMEN
        f.write("🔎 RESUMEN GENERAL\n")
        f.write("-"*60 + "\n")
        f.write(f"Total registros incluyendo  vacios o mal escritos : {metrics['total_registros']}\n")
        f.write(f"Valores únicos: {metrics['total_unicos']}\n")
        f.write(f"NaN: {metrics['null_real']}\n")
        f.write(f"Inválidos: {metrics['null_fake']}\n")
        f.write(f"Total problemáticos: {metrics['total_problemas']}\n\n")

        # TOP
        f.write("🟡 TOP VALORES\n")
        f.write("-"*60 + "\n")
        f.write(str(metrics["top_values"]) + "\n\n")

        # ENCODING
        f.write("🔴 PROBLEMAS DE ENCODING\n")
        f.write("-"*60 + "\n")
        f.write(str(metrics["encoding_issues"].head(10)) + "\n\n")

        # RAROS
        f.write("🟠 CARACTERES RAROS\n")
        f.write("-"*60 + "\n")
        f.write(str(metrics["weird_values"].head(10)) + "\n\n")

        # LONGITUD
        f.write("🔵 LONGITUD\n")
        f.write("-"*60 + "\n")
        f.write(str(metrics["lengths"]) + "\n\n")

        # TOKENS
        f.write("🟢 TOKENS\n")
        f.write("-"*60 + "\n")
        f.write(str(metrics["top_tokens"]) + "\n\n")

        f.write("="*60 + "\nFIN DEL REPORTE\n")
# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    df = load_data("data/EVOLUCION.txt")
    metrics = compute_producto_metrics(df)

    diagnose_producto(metrics)
    generate_report(metrics)