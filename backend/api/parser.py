# -*- coding: utf-8 -*-
"""
Parser de auxiliar CxC (formato EBANX) -> cuentas, facturas, totales.

Qué devuelve:
{
  "cliente": {"cliente_nombre": str|None, "cliente_rut": str|None},
  "cuentas": [
    {
      "numero_cuenta": "2-1-1-01-05",
      "nombre_cuenta": None,  # si no viene en la línea de cuenta
      "facturas": pd.DataFrame[
          # columnas pedidas:
          "numero_cuenta",
          "nombre_cuenta",
          "tipo_documento_codigo",
          "tipo_documento",
          "numero",
          "fecha_emision",
          "fecha_vcto",
          "tipo_documento_repetido",
          "numero_referencia",
          "tipo_movimiento",
          "numero_comprobante",
          "correlativo_doc_compra",
          "fecha_comprobante",
          "debe",
          "haber",
          "saldo",
          "descripcion"
      ],
      "totales_por_tipo_documento": pd.DataFrame[ "tipo_documento","debe","haber","saldo" ],
      "total_cuenta": {"debe": float, "haber": float, "saldo": float}
    }, ...
  ]
}
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import re


# ---------- Helpers ----------

ACC_CODE_RE = re.compile(r"^\s*\d[\d\-]*-\d[\d\-]*\s*$")  # detecta líneas "n° de cuenta" (debe tener al menos un guion)

def _parse_number(x) -> float:
    """Parsea números en formatos habituales (miles con . o ,; decimales con . o ,; paréntesis negativos)."""
    try:
        if pd.isna(x):
            return 0.0
    except Exception:
        pass
    s = str(x).strip()
    if not s:
        return 0.0

    negative = False
    if s.startswith("(") and s.endswith(")"):
        negative = True
        s = s[1:-1].strip()

    # quitar moneda y espacios
    s = s.replace(" ", "")
    s = re.sub(r"[^0-9,\.-]", "", s)

    if "." in s and "," in s:
        # asumir último símbolo como decimal
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        parts = s.split(",")
        if len(parts[-1]) == 3 and len(parts) > 1:
            s = s.replace(",", "")
        else:
            s = s.replace(",", ".")
    else:
        if s.count(".") > 1:
            parts = s.split(".")
            if len(parts[-1]) == 3:
                s = "".join(parts)
    try:
        val = float(s)
    except Exception:
        try:
            val = float(re.sub(r"[^\d\.-]", "", s))
        except Exception:
            return 0.0
    if negative:
        val = -val
    return float(val)

def _is_separator_or_total(val) -> bool:
    """Filas que no son movimientos: separadores, totales, vacías."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return True
    s = str(val).strip().upper()
    if not s:
        return True
    if s == "TOTAL":
        return True
    if set(s) <= set("-="):  # '-----' o '====='
        return True
    return False

def _detect_cliente(raw_df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """Detecta cliente en A1 (nombre) y A6 (RUT). Si faltan, busca heurísticamente."""
    nombre, rut = None, None
    try:
        if raw_df.shape[0] > 0 and raw_df.shape[1] > 0:
            v = raw_df.iat[0, 0]
            if isinstance(v, str) and v.strip():
                nombre = v.strip()
    except Exception:
        pass
    try:
        if raw_df.shape[0] > 5 and raw_df.shape[1] > 0:
            v = raw_df.iat[5, 0]
            if v is not None:
                rut = str(v).strip()
    except Exception:
        pass

    if not nombre:
        for i in range(min(20, len(raw_df))):
            for j in range(min(4, raw_df.shape[1])):
                val = raw_df.iat[i, j]
                if isinstance(val, str) and val.strip():
                    nombre = val.strip()
                    break
            if nombre:
                break

    RUT_RE = re.compile(r"\b\d{1,3}(?:\.\d{3})*-[\dkK]\b")
    if not rut:
        for i in range(min(40, len(raw_df))):
            for j in range(min(8, raw_df.shape[1])):
                val = str(raw_df.iat[i, j] or "")
                m = RUT_RE.search(val)
                if m:
                    rut = m.group(0)
                    break
            if rut:
                break

    return {"cliente_nombre": nombre, "cliente_rut": rut}


def _is_dash_separator(val) -> bool:
    """True si la celda es una secuencia de '-' o '=' (no cuenta vacíos)."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return False
    s = str(val).strip()
    if not s:
        return False
    return set(s) <= set("-=")


def _find_second_separator_in_col_a(raw_df: pd.DataFrame) -> Optional[int]:
    count = 0
    for i in range(len(raw_df)):
        try:
            a = raw_df.iat[i, 0]
        except Exception:
            a = None
        if _is_dash_separator(a):
            count += 1
            if count == 2:
                return i
    return None


def _safe_get(raw_df: pd.DataFrame, r: int, c: int):
    try:
        return raw_df.iat[r, c]
    except Exception:
        return None


def _read_invoices_until_blank(raw_df: pd.DataFrame, start_row: int) -> tuple[List[List[Any]], int]:
    """Lee filas desde start_row hasta la primera fila con columna A vacía. Devuelve (rows, last_row_idx)."""
    rows: List[List[Any]] = []
    idx = start_row
    n = len(raw_df)
    while idx < n:
        a = _safe_get(raw_df, idx, 0)
        if a is None or (isinstance(a, float) and pd.isna(a)) or str(a).strip() == "":
            break
        # capturar hasta 14 columnas (0..13)
        row = []
        for c in range(14):
            row.append(_safe_get(raw_df, idx, c))
        rows.append(row)
        idx += 1
    return rows, idx - 1


def _looks_like_doc_type_header(raw_df: pd.DataFrame, row_idx: int) -> bool:
    a = _safe_get(raw_df, row_idx, 0)
    b = _safe_get(raw_df, row_idx, 1)
    sa = str(a).strip() if a is not None else ""
    sb = str(b).strip() if b is not None else ""
    if not sa or not sb:
        return False
    if sa.upper() == "TOTAL":
        return False
    # Acepta códigos alfanuméricos (p. ej. '53', 'TR', 'VV') y nombre en B
    return True


def _find_next_account_or_end(raw_df: pd.DataFrame, start_row: int) -> Dict[str, Any]:
    """Busca desde start_row la próxima cuenta (código con guiones) o el total global BDO."""
    n = len(raw_df)
    for i in range(start_row, n):
        a = _safe_get(raw_df, i, 0)
        b = _safe_get(raw_df, i, 1)
        if a is None and b is None:
            continue
        sa = str(a).strip() if a is not None else ""
        sb = str(b).strip() if b is not None else ""
        if sa.upper() == "TOTAL" and "BDO" in sb.upper():
            return {"kind": "end_of_file", "row": i}
        if sa and ACC_CODE_RE.match(sa):
            return {"kind": "next_account", "row": i}
    return {"kind": "end_of_file", "row": n}


# ---------- Core ----------

def parse_auxiliar(
    excel_path: str,
    sheet_name: Optional[str] = "Ebanx LTDA",
    header_row: int = 16,
) -> Dict[str, Any]:
    """
    Parser posicional según reglas indicadas:
      - Cliente en A1 y RUT en A6.
      - Inicio análisis: fila después de la 2ª aparición de "------" (o separador de '-'/'=' en A).
      - Fila de cuenta: A = número de cuenta, C = nombre cuenta.
      - Fila de tipo: A = número tipo doc, B = nombre tipo doc.
      - Facturas: filas siguientes hasta A vacía. Luego puede venir otro tipo o el total de cuenta.
      - Siguiente cuenta: buscar siguiente código con guiones en A (se aceptan hasta 5 vacías intermedias).
      - Fin: fila con A='TOTAL' y B contiene 'BDO'.
    Devuelve el mismo formato de salida que la versión previa.
    """
    # leer crudo, sin encabezado
    raw = pd.read_excel(excel_path, sheet_name=sheet_name or 0, header=None)
    cliente = _detect_cliente(raw)

    cuentas: List[Dict[str, Any]] = []

    # buscar 2º separador
    sep_idx = _find_second_separator_in_col_a(raw)
    if sep_idx is None:
        # si no se encuentra, intentar desde el principio
        sep_idx = -1

    n = len(raw)
    cursor = sep_idx + 1  # la primera cuenta aparece justo después del 2º separador

    while cursor < n:
        acc_a = _safe_get(raw, cursor, 0)
        acc_c = _safe_get(raw, cursor, 2)
        sa = str(acc_a).strip() if acc_a is not None else ""
        if not sa or not ACC_CODE_RE.match(sa):
            # si no parece cuenta, intentar saltar a la siguiente cuenta detectada o terminar
            next_found = _find_next_account_or_end(raw, cursor)
            if next_found.get("kind") == "next_account":
                cursor = next_found.get("row")
                continue  # re-evaluar en la nueva posición
            else:
                break
        # ahora sí, tenemos cuenta
        numero_cuenta = sa
        nombre_cuenta = str(acc_c).strip() if acc_c is not None and str(acc_c).strip() != "" else None

        # mover a la fila del tipo de documento
        row_tipo = cursor + 1
        fact_rows_all: List[Dict[str, Any]] = []

        # iterar tipos de documento hasta cerrar la cuenta
        while row_tipo < n:
            # si encontramos un header de tipo (A dígitos y B texto)
            if _looks_like_doc_type_header(raw, row_tipo):
                tipo_num = str(_safe_get(raw, row_tipo, 0)).strip()
                tipo_nom = str(_safe_get(raw, row_tipo, 1)).strip()
                # facturas empiezan en la siguiente fila
                inv_start = row_tipo + 1
                rows, last_inv_row = _read_invoices_until_blank(raw, inv_start)

                # convertir a registros con columnas pedidas
                for r in rows:
                    # asegurar longitud
                    r = (r + [None] * 14)[:14]
                    fact_rows_all.append({
                        "numero_cuenta": numero_cuenta,
                        "nombre_cuenta": nombre_cuenta,
                        "tipo_documento": tipo_nom,
                        "tipo_documento_codigo": tipo_num,
                        "numero": r[1],
                        "fecha_emision": r[2],
                        "fecha_vcto": r[3],
                        "tipo_documento_repetido": r[4],
                        "numero_referencia": r[5],
                        "tipo_movimiento": r[6],
                        "numero_comprobante": r[7],
                        "correlativo_doc_compra": r[8],
                        "fecha_comprobante": r[9],
                        "debe": _parse_number(r[10]),
                        "haber": _parse_number(r[11]),
                        "saldo": _parse_number(r[12]),
                        "descripcion": r[13],
                    })

                # Escaneo flexible: saltar vacíos, saltar TOTAL del tipo, detectar nuevo tipo o total de cuenta
                idx_probe = last_inv_row + 1
                # 1) saltar filas vacías
                while idx_probe < n:
                    a = _safe_get(raw, idx_probe, 0)
                    if a is None or (isinstance(a, float) and pd.isna(a)) or str(a).strip() == "":
                        idx_probe += 1
                    else:
                        break
                if idx_probe >= n:
                    row_tipo = n
                    break
                # 2) si hay TOTAL del tipo actual, saltarlo y volver a saltar vacíos
                a = _safe_get(raw, idx_probe, 0); b = _safe_get(raw, idx_probe, 1)
                sa = str(a).strip().upper() if a is not None else ""
                sb = str(b).strip() if b is not None else ""
                if sa == "TOTAL" and sb == str(tipo_nom).strip():
                    idx_probe += 1
                    while idx_probe < n:
                        a2 = _safe_get(raw, idx_probe, 0)
                        if a2 is None or (isinstance(a2, float) and pd.isna(a2)) or str(a2).strip() == "":
                            idx_probe += 1
                        else:
                            break
                    if idx_probe >= n:
                        row_tipo = n
                        break
                    a = _safe_get(raw, idx_probe, 0); b = _safe_get(raw, idx_probe, 1)
                    sa = str(a).strip().upper() if a is not None else ""
                    sb = str(b).strip() if b is not None else ""

                # 3) decidir qué sigue
                # 3a) nuevo tipo de documento: A y B con contenido y A != TOTAL
                if _looks_like_doc_type_header(raw, idx_probe):
                    row_tipo = idx_probe
                    continue
                # 3b) total de la cuenta
                if sa == "TOTAL" and (sb == numero_cuenta or (sb and ACC_CODE_RE.match(sb))):
                    row_tipo = idx_probe + 1
                    break
                # 3c) fin global
                if sa == "TOTAL" and ("BDO" in sb.upper()):
                    row_tipo = n
                    break
                # 3d) siguiente cuenta encontrada directamente
                if str(_safe_get(raw, idx_probe, 0) or "").strip() and ACC_CODE_RE.match(str(_safe_get(raw, idx_probe, 0)).strip()):
                    row_tipo = idx_probe
                    break

                # 3e) si nada coincide, hacer lookahead amplio
                lookahead = _find_next_account_or_end(raw, idx_probe)
                if lookahead.get("kind") == "next_account":
                    row_tipo = lookahead.get("row")
                    break
                if lookahead.get("kind") == "end_of_file":
                    row_tipo = n
                    break

                # fallback: avanzar una fila para evitar bucles y continuar escaneo
                row_tipo = idx_probe + 1
                continue
            else:
                # si no es header de tipo, puede que sea fin de cuenta o ruido: intentar detectar siguiente cuenta o fin
                lookahead = _find_next_account_or_end(raw, row_tipo)
                if lookahead.get("kind") == "next_account":
                    row_tipo = lookahead.get("row")
                    break
                else:
                    # fin del archivo o no hay más
                    row_tipo = n
                    break

        # construir DataFrame de facturas y totales de la cuenta
        facturas_df = pd.DataFrame(fact_rows_all, columns=[
            "numero_cuenta","nombre_cuenta","tipo_documento_codigo","tipo_documento","numero","fecha_emision","fecha_vcto",
            "tipo_documento_repetido","numero_referencia","tipo_movimiento","numero_comprobante",
            "correlativo_doc_compra","fecha_comprobante","debe","haber","saldo","descripcion"
        ])

        # totales por tipo_documento
        if not facturas_df.empty:
            totales_tipo = (facturas_df.groupby(facturas_df["tipo_documento"].astype(str).str.strip())[["debe","haber","saldo"]]
                            .sum().reset_index().rename(columns={"tipo_documento":"tipo_documento"}))
        else:
            totales_tipo = pd.DataFrame(columns=["tipo_documento","debe","haber","saldo"])

        total_cuenta = {
            "debe":  float(facturas_df["debe"].sum()) if "debe" in facturas_df.columns else 0.0,
            "haber": float(facturas_df["haber"].sum()) if "haber" in facturas_df.columns else 0.0,
            "saldo": float(facturas_df["saldo"].sum()) if "saldo" in facturas_df.columns else 0.0,
        }

        cuentas.append({
            "numero_cuenta": numero_cuenta,
            "nombre_cuenta": nombre_cuenta,
            "facturas": facturas_df.reset_index(drop=True),
            "totales_por_tipo_documento": totales_tipo,
            "total_cuenta": total_cuenta,
        })

        # buscar siguiente cuenta a partir de la última posición procesada
        next_pos = _find_next_account_or_end(raw, row_tipo)
        if next_pos.get("kind") == "next_account":
            cursor = next_pos.get("row")
            continue
        else:
            break

    # total global sumando todas las cuentas
    total_global = {"debe": 0.0, "haber": 0.0, "saldo": 0.0}
    for acc in cuentas:
        tc = acc.get("total_cuenta") or {}
        total_global["debe"] += float(tc.get("debe", 0.0))
        total_global["haber"] += float(tc.get("haber", 0.0))
        total_global["saldo"] += float(tc.get("saldo", 0.0))

    return {"cliente": cliente, "cuentas": cuentas, "total_global": total_global}


# ------------- Ejemplo de uso -------------
if __name__ == "__main__":
    # Cambia la ruta por la tuya
    ruta = "auxiliar evanx - copia.xlsx"
    data = parse_auxiliar(ruta, sheet_name="Ebanx LTDA", header_row=16)

    print("CLIENTE:", data["cliente"])
    for acc in data["cuentas"]:
        print("\nCuenta:", acc["numero_cuenta"], "| Nombre:", acc["nombre_cuenta"])
        print("Facturas (primeras 5 filas):")
        print(acc["facturas"].head())
        print("\nTotales por tipo de documento:")
        print(acc["totales_por_tipo_documento"])
        print("\nTotal de la cuenta:", acc["total_cuenta"])

    if "total_global" in data:
        print("\n================ TOTAL GLOBAL ================")
        print(data["total_global"]) 
