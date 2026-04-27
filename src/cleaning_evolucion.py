import pandas as pd
import numpy as np
import re
import unicodedata
from collections import Counter
from openpyxl import Workbook
from openpyxl.worksheet.table import Table, TableStyleInfo


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
    
        # 🔥 NORMALIZAR COLUMNAS (CLAVE PARA EVITAR ERRORES)
    df.columns = (
        df.columns
        .str.strip()
        .str.upper()
        .str.replace(" ", "_")
    )

    
    return df



def compute_producto_metrics(df: pd.DataFrame) -> dict:
    col = df["PRODUCTO"]

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
    print("📊 DIAGNÓSTICO DE COLUMNA: PRODUCTO")
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

        f.write("📊 REPORTE DE CALIDAD DE DATOS - COLUMNA 'PRODUCTO'\n")
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
        
        
        
        
# LIMPIAR TEXTO BASE 
def normalize_text(text: str) -> str:
    if pd.isna(text):
        return None

    text = str(text)
    
    try:
        # 1. corregir encoding básico (fallback)
        text = text.encode('latin1', errors='ignore').decode('utf-8', errors='ignore')
    except:
        pass

    # 2. mayúsculas
    text = text.upper()

    # 3. quitar tildes
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ASCII', 'ignore').decode('utf-8')

    # 4. eliminar caracteres raros
    text = re.sub(r"[^A-Z0-9\s_]", " ", text)
    # 4.5 reemplazar _
    text = text.replace("_", " ")

    # 5. limpiar espacios
    text = re.sub(r"[^A-Z0-9\s_]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    

    return text if text else None

#Regex . detectar patrones
def map_producto(text: str) -> str:
        # PROTECCIÓN TOTAL
    if pd.isna(text):
        return "DESCONOCIDO"

    text = str(text).strip()

    if text in ["", "0", "NULL"]:
        return "DESCONOCIDO"

    # 🔴 CREDITO (incluye tarjetas, TC, CX)
    if re.search(r"\b(LIBRE INVERSION|CARTERA|ROTATIVO|SOBREGIROS|SOBREGRO|SOBREGIR|PRESTAMOS|PRESTAMO|LIBRE INVERSION|SOBREGIRO|CREDITO|CRED|CX|TC|TARJETA|VISA|MASTER)\b", text):
        return "CREDITO"

    # 🏠 HIPOTECARIO
    if re.search(r"FONDAVIVIENDA|HIPOTEC", text):
        return "HIPOTECARIO"

    # 🚗 VEHICULO
    if re.search(r"(SIN PRENDA|VEHICULO MOVIL SIN PRENDA|CRDITO VEHICULR|VEHICULO_SIN_PRENDA|CRDITO VEHICULR|VEHICULOS|VEHICULO|MOTO|SIN PRENDAVEHIC|SIN PRENDA|VH)", text):
        return "VEHICULO"

    # 💳 LIBRANZA
    if re.search(r"LIBRA+NZA", text):
        return "LIBRANZA"

    # 🛒 CONSUMO
    if re.search(r"CONSUMO", text):
        return "CONSUMO"

    # 🧾 ACUERDOS / CASTIGADOS
    if re.search(r"ACUERDO|CAST", text):
        return "ACUERDO_PAGO"

    # 🏫 EDUCATIVO
    if re.search(r"COLE+GIO", text):
        return "EDUCATIVO"

    # 💰 ADELANTOS
    if re.search(r"ADELANTO", text):
        return "ADELANTO"
    
    
    
    
    #siguientes categorias segun el top inicio
    
    
        # 🔹 INVERSION
    if re.search(r"FFMM", text):
        return "INVERSION"

    # 🔹 MICROCREDITO
    if re.search(r"NANO", text):
        return "MICROCREDITO"

    # 🔹 COMERCIAL
    if re.search(r"(VENTAS|RETAIL|COMERCIO)", text):
        return "COMERCIAL"

    # 🔹 LEGAL
    if re.search(r"INSOLVENCIA", text):
        return "LEGAL"

    # 🔹 BASURA → DESCONOCIDO
    if re.search(r"(GENERC?|GENERIC|M PRIVADA|M COMPARTIDA|MARCAS)", text):
        return "DESCONOCIDO"
    #otro grupo 
    # 🔹 EMPRESARIAL
    if re.search(r"PYME", text):
        return "EMPRESARIAL"

    # 🔹 GARANTIA
    if re.search(r"FNG", text):
        return "GARANTIA"

    # 🔹 BENEFICIOS
    if re.search(r"CLUB", text):
        return "BENEFICIOS"

    # 🔹 NORMALIZACION → ACUERDO
    if re.search(r"NORMALIZACION", text):
        return "ACUERDO_PAGO"

    # ⚠️ OTROS
    return "OTROS"





def limpiar_producto(df: pd.DataFrame) -> pd.DataFrame:
    df["producto_normalizado"] = df["PRODUCTO"].apply(normalize_text)
    df["producto_limpio"] = df["producto_normalizado"].apply(map_producto)

    return df

def export_to_excel(df):
    file_path = "data/EVOLUCION_LIMPIO.xlsx"

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="datos")

        ws = writer.book["datos"]

        # rango de la tabla
        rows, cols = df.shape
        table_range = f"A1:{chr(65+cols-1)}{rows+1}"

        table = Table(displayName="TablaProductos", ref=table_range)

        style = TableStyleInfo(
            name="TableStyleMedium9",
            showFirstColumn=False,
            showLastColumn=False,
            showRowStripes=True,
            showColumnStripes=False,
        )

        table.tableStyleInfo = style
        ws.add_table(table)

    print("\n✅ Excel con tabla creado:", file_path)





# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    
    # ───────── 1. CARGA ORIGINAL ─────────
    df = load_data("data/EVOLUCION.txt")
    print(df.columns.tolist()) # ver columnas
    
    
    # ───────── 2. DIAGNÓSTICO ORIGINAL ─────────
    print("\n📊 ANALISIS DATA ORIGINAL")
    metrics_original = compute_producto_metrics(df)
    diagnose_producto(metrics_original)
    generate_report(metrics_original, "report_producto_original.txt")

    # ───────── 3. LIMPIEZA ─────────
    df = limpiar_producto(df)

    # Resultados para hacer seguimiento e ir modificando con REGEX es clave TOP 20 DE 'OTROS' para ir estandarizando todo, de a grupos ─────────

    print("\n🔍 MUESTRA (ANTES vs DESPUÉS)")
    print(df[["PRODUCTO", "producto_normalizado", "producto_limpio"]].head(20))

    print("\n🔢 Valores únicos (producto_limpio):")
    print(df["producto_limpio"].nunique())

    print("\n📊 Distribución:")
    print(df["producto_limpio"].value_counts())
    
    #segunda parte . revisar categoria 'OTROS'
    print("\n🔍 TOP 20 DE 'OTROS':")
    print(
        df[df["producto_limpio"] == "OTROS"]["producto_normalizado"]
        .value_counts()
        .head(20)
)
    
    # ───4. GUARDAR LIMPIO en Excel por revision por tabla,filtros ─────
    df.to_csv("data/EVOLUCION_LIMPIO.csv", index=False, sep=";")
    print("\n✅ Archivo limpio guardado")
    
    
    # ───────── 5. DIAGNÓSTICO LIMPIO ─────────

   
    df_eval = df.copy()
    df_eval["producto"] = df_eval["producto_limpio"]

    print("\n📊 ANALISIS DATA LIMPIA")
    metrics_clean = compute_producto_metrics(df_eval)
    diagnose_producto(metrics_clean)
    generate_report(metrics_clean, "report_producto_limpio.txt")
    
    # Lo anterior  ajusto la columna producto, ve a comparar el excel 
    # 3 columnas: producto, producto normalizado, y producto limpio donde ya esta caegorizado
    
  


  