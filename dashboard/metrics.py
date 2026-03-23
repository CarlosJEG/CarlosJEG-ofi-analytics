from __future__ import annotations

import pandas as pd


def status_summary(df: pd.DataFrame) -> pd.DataFrame:
    total = len(df)
    summary = (
        df.groupby("estado", dropna=False)
        .size()
        .rename("cantidad")
        .reset_index()
        .sort_values("cantidad", ascending=False)
    )
    summary["porcentaje"] = summary["cantidad"].div(total).mul(100).round(2)
    return summary


def distribution(df: pd.DataFrame, column: str, top_n: int | None = None) -> pd.DataFrame:
    total = len(df)
    summary = (
        df.groupby(column, dropna=False)
        .size()
        .rename("cantidad")
        .reset_index()
        .sort_values(["cantidad", column], ascending=[False, True])
    )
    summary["porcentaje"] = summary["cantidad"].div(total).mul(100).round(2)
    if top_n is not None:
        summary = summary.head(top_n)
    return summary


def reception_series(df: pd.DataFrame, period: str) -> pd.DataFrame:
    column = "recepcion_dia" if period == "D" else "recepcion_mes"
    series = (
        df.dropna(subset=[column])
        .groupby(column)
        .size()
        .rename("cantidad")
        .reset_index()
        .sort_values(column)
    )
    return series


def time_metrics(df: pd.DataFrame) -> dict[str, float]:
    received = df.dropna(subset=["fecha_recepcion"])
    daily_counts = reception_series(received, "D")["cantidad"]
    monthly_counts = reception_series(received, "M")["cantidad"]

    return {
        "casos_recibidos": float(len(received)),
        "promedio_diario_recepcion": float(daily_counts.mean()) if not daily_counts.empty else 0.0,
        "promedio_mensual_recepcion": float(monthly_counts.mean()) if not monthly_counts.empty else 0.0,
        "promedio_dias_hasta_vencimiento": float(received["dias_hasta_vencimiento"].dropna().mean())
        if not received["dias_hasta_vencimiento"].dropna().empty
        else 0.0,
        "promedio_dias_hasta_respuesta": float(received["dias_hasta_respuesta"].dropna().mean())
        if not received["dias_hasta_respuesta"].dropna().empty
        else 0.0,
    }
