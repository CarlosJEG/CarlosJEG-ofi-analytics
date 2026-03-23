from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from dashboard.data import DISPLAY_COLUMNS, clean_data, load_data, load_uploaded_data
from dashboard.metrics import (
    distribution,
    reception_series,
    status_summary,
    time_metrics,
)
from dotenv import load_dotenv

load_dotenv()

APP_TITLE = os.getenv("APP_TITLE", "Dashboard de Seguimiento")
DATA_FILE = os.getenv("DATA_FILE", "").strip()
DATA_FORMAT = os.getenv("DATA_FORMAT", "csv")

st.set_page_config(page_title=APP_TITLE, layout="wide")


@st.cache_data(show_spinner=False)
def prepare_dataset() -> tuple[pd.DataFrame, object]:
    raw = load_data(DATA_FILE, DATA_FORMAT)
    return clean_data(raw)


@st.cache_data(show_spinner=False)
def prepare_uploaded_dataset(file_name: str, file_bytes: bytes) -> tuple[pd.DataFrame, object]:
    from io import BytesIO

    buffer = BytesIO(file_bytes)
    buffer.name = file_name
    raw = load_uploaded_data(buffer)
    return clean_data(raw)


def format_percent_table(df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    return df.rename(columns={dimension: "categoria"})


def resolve_dataset() -> tuple[pd.DataFrame, object, str]:
    st.sidebar.header("Fuente de datos")

    dataset_mode = "Archivo configurado"
    if DATA_FILE:
        st.sidebar.caption(f"Ruta configurada: `{DATA_FILE}`")
    else:
        st.sidebar.caption("No hay `DATA_FILE` configurado.")

    uploaded_file = st.sidebar.file_uploader(
        "Subir CSV o XLSX",
        type=["csv", "xlsx", "xls"],
        help="Util para Streamlit Cloud cuando no quieres montar un archivo en el servidor.",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        df, quality = prepare_uploaded_dataset(uploaded_file.name, file_bytes)
        return df, quality, f"Archivo subido: {uploaded_file.name}"

    if not DATA_FILE:
        raise FileNotFoundError(
            "No hay `DATA_FILE` configurado. Define esa variable o sube un archivo desde la barra lateral."
        )

    df, quality = prepare_dataset()
    return df, quality, f"Archivo configurado: {Path(DATA_FILE).name}"


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtros")

    min_date = df["fecha_recepcion"].min()
    max_date = df["fecha_recepcion"].max()
    start_date, end_date = st.sidebar.date_input(
        "Rango fecha recepcion",
        value=(min_date.date(), max_date.date()),
        min_value=min_date.date(),
        max_value=max_date.date(),
    )

    filtered = df[
        df["fecha_recepcion"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))
    ].copy()

    estado_options = sorted(filtered["estado"].dropna().unique().tolist())
    estado = st.sidebar.multiselect("Estado", estado_options, default=estado_options)
    filtered = filtered[filtered["estado"].isin(estado)]

    organismo_options = sorted(filtered["tipo_organismo"].dropna().unique().tolist())
    organismo = st.sidebar.multiselect(
        "Tipo organismo", organismo_options, default=organismo_options
    )
    filtered = filtered[filtered["tipo_organismo"].isin(organismo)]

    juzgado_options = sorted(filtered["juzgado_liquidador"].dropna().unique().tolist())
    juzgado = st.sidebar.multiselect(
        "Juzgado / Liquidador", juzgado_options, default=juzgado_options
    )
    filtered = filtered[filtered["juzgado_liquidador"].isin(juzgado)]

    tipo_options = sorted(filtered["tipo"].dropna().unique().tolist())
    tipo = st.sidebar.multiselect("Tipo", tipo_options, default=tipo_options)
    filtered = filtered[filtered["tipo"].isin(tipo)]

    responsable_options = sorted(filtered["responsable"].dropna().unique().tolist())
    responsable = st.sidebar.multiselect(
        "Responsable", responsable_options, default=responsable_options
    )
    filtered = filtered[filtered["responsable"].isin(responsable)]

    canal_options = sorted(filtered["canal"].dropna().unique().tolist())
    canal = st.sidebar.multiselect("Canal", canal_options, default=canal_options)
    filtered = filtered[filtered["canal"].isin(canal)]

    return filtered


def render_kpi_cards(df: pd.DataFrame) -> None:
    metrics = time_metrics(df)
    total = len(df)
    closed_count = int((df["estado"] == "CERRADO").sum())
    pending_count = int((df["estado"] == "PENDIENTE").sum())
    closed_pct = (closed_count / total * 100) if total else 0
    pending_pct = (pending_count / total * 100) if total else 0

    cols = st.columns(6)
    cols[0].metric("Casos filtrados", f"{total:,}".replace(",", "."))
    cols[1].metric(
        "Cerrados", f"{closed_count:,}".replace(",", "."), f"{closed_pct:.2f}%"
    )
    cols[2].metric(
        "Pendientes", f"{pending_count:,}".replace(",", "."), f"{pending_pct:.2f}%"
    )
    cols[3].metric("Promedio diario", f"{metrics['promedio_diario_recepcion']:.2f}")
    cols[4].metric("Promedio mensual", f"{metrics['promedio_mensual_recepcion']:.2f}")
    cols[5].metric(
        "Prom. recepcion a respuesta",
        f"{metrics['promedio_dias_hasta_respuesta']:.2f} dias",
    )

    cols_2 = st.columns(2)
    cols_2[0].metric(
        "Prom. recepcion a vencimiento",
        f"{metrics['promedio_dias_hasta_vencimiento']:.2f} dias",
    )
    cols_2[1].metric(
        "Casos con fecha recepcion",
        f"{int(metrics['casos_recibidos']):,}".replace(",", "."),
    )


def render_distribution_section(df: pd.DataFrame) -> None:
    st.subheader("Distribuciones")
    left, right = st.columns(2)

    with left:
        status_df = status_summary(df)
        st.markdown("**Estado**")
        st.dataframe(status_df, use_container_width=True, hide_index=True)
        st.bar_chart(status_df.set_index("estado")["cantidad"])

        org_df = distribution(df, "tipo_organismo")
        st.markdown("**Tipo de organismo**")
        st.dataframe(
            format_percent_table(org_df, "tipo_organismo"),
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(org_df.set_index("tipo_organismo")["cantidad"])

        juzgado_df = distribution(df, "juzgado_liquidador", top_n=15)
        st.markdown("**Juzgado / Liquidador (top 15)**")
        st.dataframe(
            format_percent_table(juzgado_df, "juzgado_liquidador"),
            use_container_width=True,
            hide_index=True,
        )

    with right:
        tipo_df = distribution(df, "tipo")
        st.markdown("**Tipo**")
        st.dataframe(
            format_percent_table(tipo_df, "tipo"),
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(tipo_df.set_index("tipo")["cantidad"])

        responsable_df = distribution(df, "responsable")
        st.markdown("**Responsable**")
        st.dataframe(
            format_percent_table(responsable_df, "responsable"),
            use_container_width=True,
            hide_index=True,
        )
        st.bar_chart(responsable_df.set_index("responsable")["cantidad"])

        cross = (
            df.groupby(["tipo_organismo", "juzgado_liquidador", "tipo", "responsable"])
            .size()
            .rename("cantidad")
            .reset_index()
            .sort_values("cantidad", ascending=False)
            .head(20)
        )
        st.markdown("**Relacion organismo -> juzgado -> tipo -> responsable (top 20)**")
        st.dataframe(cross, use_container_width=True, hide_index=True)


def render_time_section(df: pd.DataFrame) -> None:
    st.subheader("KPIs de Fechas")
    daily = reception_series(df, "D")
    monthly = reception_series(df, "M")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Cantidad diaria por fecha de recepcion**")
        if daily.empty:
            st.info("No hay datos para el rango filtrado.")
        else:
            st.line_chart(daily.set_index("recepcion_dia")["cantidad"])
            st.dataframe(daily, use_container_width=True, hide_index=True)

    with col2:
        st.markdown("**Cantidad mensual por fecha de recepcion**")
        if monthly.empty:
            st.info("No hay datos para el rango filtrado.")
        else:
            st.bar_chart(monthly.set_index("recepcion_mes")["cantidad"])
            st.dataframe(monthly, use_container_width=True, hide_index=True)

    delta_cols = st.columns(2)
    with delta_cols[0]:
        venc = (
            df.dropna(
                subset=[
                    "fecha_recepcion",
                    "fecha_vencimiento",
                    "dias_hasta_vencimiento",
                ]
            )
            .loc[
                :,
                [
                    "caso",
                    "fecha_recepcion",
                    "fecha_vencimiento",
                    "dias_hasta_vencimiento",
                ],
            ]
            .sort_values("fecha_recepcion", ascending=False)
        )
        st.markdown("**Fecha recepcion vs fecha vencimiento**")
        st.dataframe(
            venc.rename(columns=DISPLAY_COLUMNS),
            use_container_width=True,
            hide_index=True,
        )

    with delta_cols[1]:
        respuesta = (
            df.dropna(
                subset=["fecha_recepcion", "fecha_respuesta", "dias_hasta_respuesta"]
            )
            .loc[
                :,
                ["caso", "fecha_recepcion", "fecha_respuesta", "dias_hasta_respuesta"],
            ]
            .sort_values("fecha_recepcion", ascending=False)
        )
        st.markdown("**Fecha recepcion vs fecha respuesta**")
        st.dataframe(
            respuesta.rename(columns=DISPLAY_COLUMNS),
            use_container_width=True,
            hide_index=True,
        )


def main() -> None:
    try:
        df, quality, source_label = resolve_dataset()
    except Exception as exc:
        st.title(APP_TITLE)
        st.error("No fue posible cargar el dataset.")
        st.exception(exc)
        st.info(
            "Configura `DATA_FILE` en el entorno o sube un archivo `csv`/`xlsx` desde la barra lateral."
        )
        return

    filtered = apply_filters(df)

    st.title(APP_TITLE)
    st.caption(
        f"Fuente: {source_label} | Registros cargados: {quality.total_rows} | "
        f"Casos con fechas invalidas convertidas a nulo: {quality.invalid_date_rows}"
    )

    if quality.invalid_date_cases:
        st.warning(
            "Se detectaron fechas fuera de rango y se trataron como nulas en los casos: "
            + ", ".join(quality.invalid_date_cases)
        )

    render_kpi_cards(filtered)
    render_distribution_section(filtered)
    render_time_section(filtered)

    st.subheader("Detalle")
    detail_columns = [
        "caso",
        "estado",
        "tipo_organismo",
        "juzgado_liquidador",
        "tipo",
        "responsable",
        "canal",
        "fecha_recepcion",
        "fecha_vencimiento",
        "fecha_respuesta",
        "dias_hasta_vencimiento",
        "dias_hasta_respuesta",
    ]
    st.dataframe(
        filtered.loc[:, detail_columns].rename(columns=DISPLAY_COLUMNS),
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()
