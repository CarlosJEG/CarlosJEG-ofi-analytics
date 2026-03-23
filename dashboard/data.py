from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

REQUIRED_SOURCE_COLUMNS = {
    "CASO",
    "ESTADO",
    "FECHA_RECEPCION",
    "FECHA_VENCIMIENTO",
    "TIPO_ORGANISMO",
    "JUZGADO / LIQUIDADOR",
    "TIPO",
    "RESPONSABLE",
    "FECHA_RESPUESTA",
    "CANAL",
}

DATE_COLUMNS = [
    "fecha_oficio",
    "fecha_recepcion",
    "fecha_vencimiento",
    "fecha_solicitud_informacion",
    "fecha_respuesta",
]

TEXT_COLUMNS = [
    "estado",
    "tipo_organismo",
    "juzgado_liquidador",
    "tipo",
    "responsable",
    "canal",
    "modo_envio",
    "observaciones",
    "nombre",
    "rut",
    "rit_ruc_rol",
    "n_caso_salesforce",
    "n_oficio",
]

RENAME_MAP = {
    "CASO": "caso",
    "ESTADO": "estado",
    "ALERTA": "alerta",
    "FECHA_OFICIO": "fecha_oficio",
    "FECHA_RECEPCION": "fecha_recepcion",
    "PLAZO_DIAS_HABILES_BANCARIOS": "plazo_dias_habiles_bancarios",
    "FECHA_VENCIMIENTO": "fecha_vencimiento",
    "N°_CASO_SALESFORCE": "n_caso_salesforce",
    "N°_OFICIO": "n_oficio",
    "RIT_RUC_ROL": "rit_ruc_rol",
    "TIPO_ORGANISMO": "tipo_organismo",
    "JUZGADO / LIQUIDADOR": "juzgado_liquidador",
    "FECHA_SOLICITUD_INFORMACION": "fecha_solicitud_informacion",
    "NOMBRE": "nombre",
    "RUT": "rut",
    "MODO_ENVIO": "modo_envio",
    "OBSERVACIONES": "observaciones",
    "TIPO": "tipo",
    "RESPONSABLE": "responsable",
    "FECHA_RESPUESTA": "fecha_respuesta",
    "CANAL": "canal",
}

DISPLAY_COLUMNS = {
    "caso": "Caso",
    "estado": "Estado",
    "tipo_organismo": "Tipo organismo",
    "juzgado_liquidador": "Juzgado / Liquidador",
    "tipo": "Tipo",
    "responsable": "Responsable",
    "canal": "Canal",
    "fecha_recepcion": "Fecha recepcion",
    "fecha_vencimiento": "Fecha vencimiento",
    "fecha_respuesta": "Fecha respuesta",
    "dias_hasta_vencimiento": "Dias recepcion a vencimiento",
    "dias_hasta_respuesta": "Dias recepcion a respuesta",
}


@dataclass(frozen=True)
class DataQuality:
    total_rows: int
    invalid_date_rows: int
    invalid_date_cases: list[str]


def load_data(path: str | Path, data_format: str | None = None) -> pd.DataFrame:
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"No se encontro el archivo de datos: {file_path}")
    file_format = (data_format or file_path.suffix.lstrip(".")).lower()
    if file_format == "csv":
        return pd.read_csv(file_path, sep=";", encoding="utf-8-sig")
    if file_format in {"xlsx", "xls"}:
        return pd.read_excel(file_path, sheet_name=0)
    raise ValueError(f"Formato no soportado: {file_format}")


def load_uploaded_data(uploaded_file) -> pd.DataFrame:
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file, sep=";", encoding="utf-8-sig")
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file, sheet_name=0)
    raise ValueError("Formato no soportado. Sube un archivo CSV o XLSX.")


def validate_source_columns(df: pd.DataFrame) -> None:
    missing_columns = sorted(REQUIRED_SOURCE_COLUMNS - set(df.columns))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ValueError(f"Faltan columnas requeridas en el dataset: {missing}")


def clean_data(df: pd.DataFrame) -> tuple[pd.DataFrame, DataQuality]:
    validate_source_columns(df)
    clean = df.rename(columns=RENAME_MAP).copy()

    for column in TEXT_COLUMNS:
        if column in clean.columns:
            clean[column] = clean[column].fillna("").astype(str).str.strip()
            clean[column] = clean[column].replace({"nan": "", "None": ""})

    clean["estado"] = clean["estado"].str.upper()
    clean["caso"] = pd.to_numeric(clean["caso"], errors="coerce").astype("Int64")
    clean["plazo_dias_habiles_bancarios"] = pd.to_numeric(
        clean["plazo_dias_habiles_bancarios"], errors="coerce"
    )

    invalid_cases: set[str] = set()
    for column in DATE_COLUMNS:
        if column not in clean.columns:
            continue
        numeric_dates = pd.to_numeric(clean[column], errors="coerce")
        parsed = pd.to_datetime(numeric_dates, unit="D", origin="1899-12-30", errors="coerce")
        invalid_mask = parsed.notna() & (
            (parsed.dt.year < 2020) | (parsed.dt.year > 2035)
        )
        invalid_cases.update(clean.loc[invalid_mask, "caso"].astype(str).tolist())
        parsed = parsed.mask(invalid_mask)
        clean[column] = parsed

    clean["tipo_organismo"] = clean["tipo_organismo"].replace("", "Sin clasificar")
    clean["juzgado_liquidador"] = clean["juzgado_liquidador"].replace("", "Sin clasificar")
    clean["tipo"] = clean["tipo"].replace("", "Sin clasificar")
    clean["responsable"] = clean["responsable"].replace("", "Sin asignar")
    clean["canal"] = clean["canal"].replace("", "Sin canal")

    clean["dias_hasta_vencimiento"] = (
        clean["fecha_vencimiento"] - clean["fecha_recepcion"]
    ).dt.days
    clean["dias_hasta_respuesta"] = (
        clean["fecha_respuesta"] - clean["fecha_recepcion"]
    ).dt.days
    clean["recepcion_dia"] = clean["fecha_recepcion"].dt.normalize()
    clean["recepcion_mes"] = clean["fecha_recepcion"].dt.to_period("M").dt.to_timestamp()

    quality = DataQuality(
        total_rows=len(clean),
        invalid_date_rows=len(invalid_cases),
        invalid_date_cases=sorted(invalid_cases),
    )
    return clean, quality
