import io
import math
import re
from datetime import datetime

import pandas as pd
import streamlit as st

try:
    from ValidacionDeDatos.styles import render_metric, setup_styles
    from ValidacionDeDatos.validation_logic import (
        CECO_EVALUATED_COL,
        CECO_EVALUATED_COUNT_COL,
        detect_file_dates,
        suggest_columns,
        summarize_validation,
        validate_people_ceco_activity,
    )
except ImportError:
    from styles import render_metric, setup_styles
    from validation_logic import (
        CECO_EVALUATED_COL,
        CECO_EVALUATED_COUNT_COL,
        detect_file_dates,
        suggest_columns,
        summarize_validation,
        validate_people_ceco_activity,
    )


STATS_STATE_KEY = "vd_stats_df"
DATES_STATE_KEY = "vd_file_dates"
CONFIG_STATE_KEY = "vd_last_config"
HIDDEN_STATE_KEY = "vd_hidden_neutral_rows"


@st.cache_data
def load_excel(file):
    try:
        return pd.read_excel(file, engine="openpyxl")
    except Exception as exc:
        st.error(f"Error al cargar el archivo: {exc}")
        return None


def _safe_index(options: list, value, fallback: int = 0) -> int:
    try:
        return options.index(value)
    except ValueError:
        return fallback


def _build_optional_options(df: pd.DataFrame, suggested_col: str | None) -> tuple[list, int]:
    options = ["Ninguna"] + df.columns.tolist()
    default = _safe_index(options, suggested_col, fallback=0) if suggested_col else 0
    return options, default


def _contains_text(series: pd.Series, query: str) -> pd.Series:
    if not query:
        return pd.Series([True] * len(series), index=series.index)
    escaped_query = re.escape(query.strip().lower())
    values = series.fillna("").astype(str).str.lower()
    return values.str.contains(escaped_query, regex=True)


def _render_section_header(title: str, subtitle: str = "") -> None:
    subtitle_html = f'<p class="subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
<div class="vd-section">
    <p class="title">{title}</p>
    {subtitle_html}
</div>
""",
        unsafe_allow_html=True,
    )


def _apply_quick_filter(df: pd.DataFrame, quick_filter: str) -> pd.DataFrame:
    if quick_filter == "Solo con problemas":
        return df[df["Tiene Problemas"].astype(bool)]
    if quick_filter == "Solo CECO diferentes":
        return df[df["Cecos Diferentes"].astype(bool)]
    if quick_filter == "Solo con vacios":
        return df[df["Tiene Ceco Vacio"] | df["Tiene Actividad Vacia"]]
    if quick_filter == "Solo con omitidas CECO" and "Filas Omitidas CECO" in df.columns:
        return df[df["Filas Omitidas CECO"] > 0]
    return df


def _render_instructions() -> None:
    _render_section_header("Como usar", "Flujo rapido en 4 pasos")
    st.markdown(
        """
1. Sube el archivo Excel de la fecha a validar.  
2. Revisa la configuracion sugerida de columnas.  
3. Haz clic en **Procesar validacion**.  
4. Usa la busqueda y filtros rapidos para encontrar casos y exportar.
"""
    )


def _render_preview(df: pd.DataFrame) -> None:
    _render_section_header("Vista previa", "Confirma que el archivo se cargo correctamente")
    st.markdown(
        f"""
<div style="margin: 0.5rem 0 1rem; color: #94a3b8;">
Archivo cargado: <strong>{len(df)}</strong> filas, <strong>{len(df.columns)}</strong> columnas
</div>
""",
        unsafe_allow_html=True,
    )
    with st.expander("Vista previa", expanded=False):
        st.dataframe(df.head(15), use_container_width=True)


def _render_configuration(df: pd.DataFrame) -> dict[str, str]:
    suggestions = suggest_columns(df)
    all_columns = df.columns.tolist()

    _render_section_header("Configuracion", "Selecciona columnas principales y opcionales")
    col1, col2, col3 = st.columns(3)

    with col1:
        person_col = st.selectbox(
            "Columna de Persona",
            options=all_columns,
            index=_safe_index(all_columns, suggestions["persona"]),
        )

    with col2:
        ceco_default = suggestions["ceco"] if suggestions["ceco"] else all_columns[0]
        ceco_col = st.selectbox(
            "Columna de CECO",
            options=all_columns,
            index=_safe_index(all_columns, ceco_default),
        )

    with col3:
        activity_default = suggestions["actividad"] if suggestions["actividad"] else all_columns[0]
        activity_col = st.selectbox(
            "Columna de Actividad",
            options=all_columns,
            index=_safe_index(all_columns, activity_default),
        )

    col4, col5, col6 = st.columns(3)
    with col4:
        doc_options, doc_default = _build_optional_options(df, suggestions["documento"])
        document_col = st.selectbox(
            "Columna de Documento (opcional)",
            options=doc_options,
            index=doc_default,
        )
    with col5:
        date_options, date_default = _build_optional_options(df, suggestions["fecha"])
        date_col = st.selectbox(
            "Columna de Fecha (opcional)",
            options=date_options,
            index=date_default,
            help="Si la seleccionas, se valida tambien si el archivo trae una sola fecha.",
        )
    with col6:
        code_options, code_default = _build_optional_options(df, suggestions["cod_actividad"])
        activity_code_col = st.selectbox(
            "Columna Cod. Actividad (opcional)",
            options=code_options,
            index=code_default,
            help="Si la seleccionas, Actividad Diferente y omision de CECO consideraran este codigo.",
        )

    return {
        "person_col": person_col,
        "ceco_col": ceco_col,
        "activity_col": activity_col,
        "document_col": document_col if document_col != "Ninguna" else None,
        "date_col": date_col if date_col != "Ninguna" else None,
        "activity_code_col": activity_code_col if activity_code_col != "Ninguna" else None,
    }


def _run_validation(df: pd.DataFrame, config: dict[str, str]) -> None:
    stats_df = validate_people_ceco_activity(
        df=df,
        person_col=config["person_col"],
        ceco_col=config["ceco_col"],
        activity_col=config["activity_col"],
        date_col=config["date_col"],
        document_col=config["document_col"],
        activity_code_col=config["activity_code_col"],
    )
    hidden_neutral_rows = 0
    if CECO_EVALUATED_COUNT_COL in stats_df.columns and "Tiene Problemas" in stats_df.columns:
        neutral_mask = (stats_df[CECO_EVALUATED_COUNT_COL] == 0) & (~stats_df["Tiene Problemas"])
        hidden_neutral_rows = int(neutral_mask.sum())
        stats_df = stats_df[~neutral_mask].reset_index(drop=True)

    file_dates = detect_file_dates(df, config["date_col"])
    st.session_state[STATS_STATE_KEY] = stats_df
    st.session_state[DATES_STATE_KEY] = file_dates
    st.session_state[CONFIG_STATE_KEY] = config
    st.session_state[HIDDEN_STATE_KEY] = hidden_neutral_rows


def _render_summary(stats_df: pd.DataFrame, file_dates: list[str]) -> None:
    _render_section_header("Resumen general", "Indicadores principales de la validacion")
    summary = summarize_validation(stats_df, file_dates)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric("Total personas", summary["total_personas"])
    with m2:
        render_metric("Con problemas", summary["con_problemas"], tone="danger")
    with m3:
        render_metric("CECO diferentes", summary["cecos_diferentes"], tone="warning")
    with m4:
        render_metric("Con vacios", summary["con_vacios"], tone="danger")

    if file_dates:
        if len(file_dates) > 1:
            st.warning(
                f"Se detectaron multiples fechas en el archivo ({len(file_dates)}): {', '.join(file_dates)}"
            )
        else:
            st.success(f"Fecha unica detectada en archivo: {file_dates[0]}")

    hidden_neutral_rows = int(st.session_state.get(HIDDEN_STATE_KEY, 0))
    if hidden_neutral_rows > 0:
        st.info(
            f"Se ocultaron {hidden_neutral_rows} registros sin CECO evaluable y sin problemas (no aplican a validacion)."
        )


def _render_results_table(stats_df: pd.DataFrame) -> pd.DataFrame:
    _render_section_header(
        "Resultados de validacion",
        "Busqueda rapida + filtro rapido. Lo avanzado esta en el desplegable.",
    )

    top1, top2, top3 = st.columns([2, 1.2, 0.8])
    with top1:
        search_query = st.text_input(
            "Buscar en tabla",
            value="",
            placeholder="Persona, documento, CECO, actividad, observaciones...",
        )
    with top2:
        quick_filter = st.selectbox(
            "Filtro rapido",
            options=[
                "Todos",
                "Solo con problemas",
                "Solo CECO diferentes",
                "Solo con vacios",
                "Solo con omitidas CECO",
            ],
            index=0,
        )
    with top3:
        rows_per_page = st.selectbox("Filas", options=[25, 50, 100, 200], index=1)

    with st.expander("Filtros avanzados (opcional)", expanded=False):
        a1, a2 = st.columns(2)
        with a1:
            ceco_query = st.text_input("Contiene CECO", value="", placeholder="Ej: CAM-007")
        with a2:
            activity_query = st.text_input("Contiene Actividad", value="", placeholder="Ej: PODADOR")

        a3, a4 = st.columns(2)
        sort_options = [
            col
            for col in ["Persona", "Tiene Problemas", "Filas Persona", "Filas Omitidas CECO"]
            if col in stats_df.columns
        ]
        if not sort_options:
            sort_options = [stats_df.columns[0]]
        with a3:
            sort_by = st.selectbox("Ordenar por", options=sort_options, index=0)
        with a4:
            ascending = st.checkbox("Orden ascendente", value=True)

    filtered_df = stats_df.copy()
    filtered_df = _apply_quick_filter(filtered_df, quick_filter)

    if search_query.strip():
        search_cols = [
            "Persona",
            "Documento",
            "Cecos Unicos",
            CECO_EVALUATED_COL,
            "Actividades Unicas",
            "Actividades (con Cod. Actividad)",
            "Observaciones",
        ]
        search_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
        for col in search_cols:
            if col in filtered_df.columns:
                search_mask = search_mask | _contains_text(filtered_df[col], search_query)
        filtered_df = filtered_df[search_mask]

    if ceco_query.strip() and "Cecos Unicos" in filtered_df.columns:
        filtered_df = filtered_df[_contains_text(filtered_df["Cecos Unicos"], ceco_query)]

    if activity_query.strip():
        activity_mask = pd.Series([False] * len(filtered_df), index=filtered_df.index)
        if "Actividades Unicas" in filtered_df.columns:
            activity_mask = activity_mask | _contains_text(filtered_df["Actividades Unicas"], activity_query)
        if "Actividades (con Cod. Actividad)" in filtered_df.columns:
            activity_mask = activity_mask | _contains_text(
                filtered_df["Actividades (con Cod. Actividad)"], activity_query
            )
        filtered_df = filtered_df[activity_mask]

    if sort_by in filtered_df.columns:
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=ascending, kind="stable")

    show_cols = [
        "Persona",
        "Documento",
        "Filas Persona",
        "Cecos Unicos",
        CECO_EVALUATED_COL,
        "Filas Omitidas CECO",
        "Actividades Unicas",
        "Actividades (con Cod. Actividad)",
        "Ceco Vacio (filas)",
        "Actividad Vacia (filas)",
        "Fechas Persona",
        "Observaciones",
        "Tiene Problemas",
    ]
    show_cols = [col for col in show_cols if col in filtered_df.columns]

    if filtered_df.empty:
        st.info("No hay registros para mostrar con esos filtros.")
        return filtered_df

    p1, p2 = st.columns([1, 2])
    total_rows = len(filtered_df)
    total_pages = max(1, math.ceil(total_rows / rows_per_page))
    with p1:
        page = st.number_input("Pagina", min_value=1, max_value=total_pages, value=1, step=1)
    start = (int(page) - 1) * rows_per_page
    end = min(start + rows_per_page, total_rows)
    with p2:
        st.caption(f"Mostrando {start + 1}-{end} de {total_rows} registros. Filtro rapido: {quick_filter}.")

    page_df = filtered_df.iloc[start:end][show_cols]
    st.dataframe(page_df, use_container_width=True, height=420)
    return filtered_df


def _render_person_detail(stats_df: pd.DataFrame) -> None:
    _render_section_header("Detalle por persona", "Busca por nombre y revisa el detalle del registro")
    person_search = st.text_input(
        "Buscar persona para detalle",
        value="",
        placeholder="Escribe nombre o parte del nombre",
        help="No necesitas seleccionar DNI para encontrar una persona.",
    )
    detail_df = stats_df.copy()
    if person_search.strip():
        detail_df = detail_df[_contains_text(detail_df["Persona"], person_search)]
    if detail_df.empty:
        st.info("No se encontro persona para el termino de busqueda.")
        return

    person_options = detail_df["Persona"].astype(str).tolist()
    selected_person = st.selectbox("Selecciona una persona", options=person_options)
    person_data = detail_df[detail_df["Persona"] == selected_person].iloc[0]

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Filas de la persona", int(person_data["Filas Persona"]))
    with c2:
        st.metric("Cecos unicos", int(person_data["Cantidad Cecos Unicos"]))
    with c3:
        st.metric("Actividades unicas", int(person_data["Cantidad Actividades Unicas"]))

    st.markdown(
        f"""
**Documento:** {person_data.get("Documento", "N/A")}  
**CECOs:** {person_data["Cecos Unicos"]}  
**CECOs evaluados (sin actividades omitidas):** {person_data.get(CECO_EVALUATED_COL, "Ninguno")}  
**Filas omitidas para CECO:** {person_data.get("Filas Omitidas CECO", 0)}  
**Actividades:** {person_data["Actividades Unicas"]}  
**Actividades con codigo:** {person_data.get("Actividades (con Cod. Actividad)", "Ninguna")}  
**Fechas:** {person_data["Fechas Persona"]}  
**Observaciones:** {person_data["Observaciones"]}
"""
    )


def _build_export_dataframe(df: pd.DataFrame, for_excel: bool = True) -> pd.DataFrame:
    preferred_cols = [
        "Persona",
        "Documento",
        "Cecos Unicos",
        "Actividades Unicas",
        "Ceco Vacio (filas)",
        "Actividad Vacia (filas)",
        "Cecos Diferentes",
        "Filas Omitidas CECO",
        "Observaciones",
        "Tiene Problemas",
    ]
    cols = [col for col in preferred_cols if col in df.columns]
    export_df = df[cols].copy() if cols else df.copy()

    if not for_excel:
        return export_df

    if "Cecos Diferentes" in export_df.columns:
        export_df["Cecos Diferentes"] = export_df["Cecos Diferentes"].map(
            lambda x: "SI" if bool(x) else "NO"
        )
    if "Tiene Problemas" in export_df.columns:
        export_df["Tiene Problemas"] = export_df["Tiene Problemas"].map(
            lambda x: "SI" if bool(x) else "NO"
        )
    return export_df


def _render_observations_view(stats_df: pd.DataFrame) -> None:
    _render_section_header(
        "Vista de observaciones",
        "Solo registros con problemas (CECO diferentes o vacios). Aqui puedes revisar y descargar el Excel.",
    )
    if "Tiene Problemas" not in stats_df.columns:
        st.info("No hay columna de problemas en los datos.")
        return

    problems_df = stats_df[stats_df["Tiene Problemas"].astype(bool)].copy()
    if problems_df.empty:
        st.success("No hay observaciones: nadie tiene CECO diferentes ni vacios.")
        return

    view_cols = [
        "Persona",
        "Documento",
        "Cecos Unicos",
        "Ceco Vacio (filas)",
        "Actividad Vacia (filas)",
        "Filas Omitidas CECO",
        "Observaciones",
    ]
    view_cols = [c for c in view_cols if c in problems_df.columns]
    st.dataframe(problems_df[view_cols], use_container_width=True, height=400)
    st.caption(f"Total: {len(problems_df)} registros con observaciones.")

    export_df = _build_export_dataframe(problems_df, for_excel=True)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Observaciones")

    st.download_button(
        label="Descargar Excel con observaciones",
        data=buf.getvalue(),
        file_name=f"observaciones_ceco_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _render_export(stats_df: pd.DataFrame) -> None:
    _render_section_header(
        "Exportar resultados",
        "Descarga la validacion completa en Excel (vista limpia).",
    )
    export_all_df = _build_export_dataframe(stats_df, for_excel=True)
    full_output = io.BytesIO()
    with pd.ExcelWriter(full_output, engine="openpyxl") as writer:
        export_all_df.to_excel(writer, index=False, sheet_name="Validacion")

    st.download_button(
        label="Descargar validacion completa (Excel)",
        data=full_output.getvalue(),
        file_name=f"validacion_ceco_actividad_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def run_app():
    setup_styles()

    uploaded_file = st.file_uploader(
        "Sube el archivo Excel",
        type=["xlsx", "xls"],
        help="Archivo con registros para validar CECO y Actividad por persona.",
    )

    if uploaded_file is None:
        _render_instructions()
        return

    df = load_excel(uploaded_file)
    if df is None:
        return
    if df.empty:
        st.warning("El archivo esta vacio.")
        return

    _render_preview(df)
    config = _render_configuration(df)

    if st.button("Procesar validacion", type="primary"):
        try:
            _run_validation(df, config)
            st.success("Validacion completada.")
        except ValueError as exc:
            st.error(str(exc))
        except Exception as exc:
            st.error(f"Ocurrio un error durante la validacion: {exc}")

    if STATS_STATE_KEY not in st.session_state:
        return

    stats_df = st.session_state[STATS_STATE_KEY]
    file_dates = st.session_state.get(DATES_STATE_KEY, [])

    _render_summary(stats_df, file_dates)
    filtered_df = _render_results_table(stats_df)

    _render_observations_view(stats_df)

    if filtered_df.empty:
        st.info("No hay registros para mostrar con los filtros actuales.")
    else:
        _render_person_detail(filtered_df)

    _render_export(stats_df)


if __name__ == "__main__":
    run_app()
