import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import date


def _normalizar_fecha(series: pd.Series) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce", dayfirst=True)
    normalized = dt.dt.strftime("%Y-%m-%d")
    invalid_mask = normalized.isna() | (normalized == "NaT")
    if invalid_mask.any():
        normalized.loc[invalid_mask] = series.loc[invalid_mask].astype(str).str.strip().str[:10]
    return normalized.fillna("").replace({"NaT": "", "nan": "", "None": ""})


def _filtrar_por_rango_fecha(df: pd.DataFrame, fecha_col: str | None, fecha_inicio: date | None, fecha_fin: date | None) -> pd.DataFrame:
    if not fecha_col or fecha_col not in df.columns:
        return df
    if not fecha_inicio or not fecha_fin:
        return df

    fechas_norm = _normalizar_fecha(df[fecha_col])
    fechas_dt = pd.to_datetime(fechas_norm, errors="coerce")
    inicio = pd.Timestamp(fecha_inicio)
    fin = pd.Timestamp(fecha_fin)
    mask = fechas_dt.notna() & (fechas_dt >= inicio) & (fechas_dt <= fin)
    return df[mask].copy()


def procesar_archivos(
    archivo_global,
    archivo_filtro,
    fecha_global_col=None,
    fecha_filtro_col=None,
    fecha_inicio: date | None = None,
    fecha_fin: date | None = None,
):
    # Leer Excels
    df_global = pd.read_excel(archivo_global, dtype=str)
    df_filtro = pd.read_excel(archivo_filtro, dtype=str)

    col_global = "NRO. DOCUMENTO"
    col_filtro = "DNI"

    # Validar columnas
    if col_global not in df_global.columns:
        raise ValueError(
            f"En la DATA GLOBAL no se encontró la columna '{col_global}'. "
            f"Columnas disponibles: {list(df_global.columns)}"
        )
    if col_filtro not in df_filtro.columns:
        raise ValueError(
            f"En el archivo de DNIs no se encontró la columna '{col_filtro}'. "
            f"Columnas disponibles: {list(df_filtro.columns)}"
        )
    if fecha_global_col and fecha_global_col not in df_global.columns:
        raise ValueError(
            f"En la DATA GLOBAL no se encontró la columna de fecha '{fecha_global_col}'. "
            f"Columnas disponibles: {list(df_global.columns)}"
        )
    if fecha_filtro_col and fecha_filtro_col not in df_filtro.columns:
        raise ValueError(
            f"En el archivo de filtro no se encontró la columna de fecha '{fecha_filtro_col}'. "
            f"Columnas disponibles: {list(df_filtro.columns)}"
        )

    # Normalizar
    df_global[col_global] = df_global[col_global].astype(str).str.strip()
    df_filtro[col_filtro] = df_filtro[col_filtro].astype(str).str.strip()

    # Filtrar por rango de fechas (si se configuró en cada archivo)
    df_global = _filtrar_por_rango_fecha(df_global, fecha_global_col, fecha_inicio, fecha_fin)
    df_filtro = _filtrar_por_rango_fecha(df_filtro, fecha_filtro_col, fecha_inicio, fecha_fin)

    # Columna común para merge
    df_global["DNI_MERGE"] = df_global[col_global]
    df_filtro["DNI_MERGE"] = df_filtro[col_filtro]

    # Merge
    df_merge = df_filtro.merge(
        df_global,
        on="DNI_MERGE",
        how="left",
        indicator=True
    )

    # Encontrados: nos quedamos solo con registros que hacen match
    df_encontrados = df_merge[df_merge["_merge"] == "both"].copy()

    # Eliminamos columnas auxiliares para que la data quede "limpia"
    cols_aux = ["_merge", "DNI_MERGE"]
    df_encontrados = df_encontrados.drop(columns=cols_aux, errors="ignore")

    # No encontrados
    df_no_encontrados = (
        df_merge[df_merge["_merge"] == "left_only"][["DNI_MERGE"]]
        .drop_duplicates()
        .rename(columns={"DNI_MERGE": col_filtro})
    )
    df_no_encontrados["MENSAJE"] = "DNI no se encontró en la data global filtrada"

    return df_encontrados, df_no_encontrados

def df_a_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output


def run_app():
    st.title("Filtro de DNIs contra data global")

    st.write(
        """
    Sube tu **data global** (con muchos registros) y tu archivo de **DNIs a buscar**.
    El sistema comparará:
    - Columna `NRO. DOCUMENTO` en la data global
    - Columna `DNI` en la data reducida
    - Opcionalmente, filtrará ambos archivos por un rango de fechas
    y generará archivos para descargar con los resultados.
    """
    )

    # Carga de archivos
    archivo_global = st.file_uploader(
        "Sube el Excel de la DATA GLOBAL (columna 'NRO. DOCUMENTO')",
        type=["xlsx"],
        key="global",
    )
    archivo_filtro = st.file_uploader(
        "Sube el Excel con la LISTA DE DNIs (columna 'DNI')",
        type=["xlsx"],
        key="filtro",
    )

    if archivo_global is not None and archivo_filtro is not None:
        df_global_preview = pd.read_excel(archivo_global, nrows=0)
        archivo_global.seek(0)
        df_filtro_preview = pd.read_excel(archivo_filtro, nrows=0)
        archivo_filtro.seek(0)

        fecha_global_options = ["(No filtrar por fecha)"] + list(df_global_preview.columns)
        fecha_filtro_options = ["(No filtrar por fecha)"] + list(df_filtro_preview.columns)

        c1, c2 = st.columns(2)
        with c1:
            fecha_global_sel = st.selectbox(
                "Columna de fecha en DATA GLOBAL (opcional)",
                options=fecha_global_options,
                index=0,
            )
        with c2:
            fecha_filtro_sel = st.selectbox(
                "Columna de fecha en archivo de DNIs (opcional)",
                options=fecha_filtro_options,
                index=0,
            )

        fecha_global_col = None if fecha_global_sel == "(No filtrar por fecha)" else fecha_global_sel
        fecha_filtro_col = None if fecha_filtro_sel == "(No filtrar por fecha)" else fecha_filtro_sel

        st.markdown("### Rango de fecha para filtrar")
        hoy = date.today()
        r1, r2 = st.columns(2)
        with r1:
            fecha_inicio = st.date_input("Desde", value=hoy)
        with r2:
            fecha_fin = st.date_input("Hasta", value=hoy)

        if fecha_inicio > fecha_fin:
            st.warning("La fecha inicial no puede ser mayor que la fecha final.")

        if st.button("Procesar archivos"):
            try:
                if fecha_inicio > fecha_fin:
                    raise ValueError("La fecha inicial no puede ser mayor que la fecha final.")

                df_encontrados, df_no_encontrados = procesar_archivos(
                    archivo_global,
                    archivo_filtro,
                    fecha_global_col=fecha_global_col,
                    fecha_filtro_col=fecha_filtro_col,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                )

                st.success("Procesamiento completado.")

                # Mostrar resumen
                st.write(f"Registros encontrados: **{len(df_encontrados)}**")
                st.write(f"DNIs no encontrados: **{len(df_no_encontrados)}**")

                # Vista previa
                if not df_encontrados.empty:
                    st.subheader("Vista previa de registros encontrados")
                    st.dataframe(df_encontrados.head(20))

                if not df_no_encontrados.empty:
                    st.subheader("DNIs no encontrados")
                    st.dataframe(df_no_encontrados.head(20))

                # Botones de descarga
                if not df_encontrados.empty:
                    excel_encontrados = df_a_excel_bytes(df_encontrados)
                    st.download_button(
                        label="📥 Descargar registros ENCONTRADOS (Excel)",
                        data=excel_encontrados,
                        file_name="resultado_encontrados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                if not df_no_encontrados.empty:
                    excel_no_encontrados = df_a_excel_bytes(df_no_encontrados)
                    st.download_button(
                        label="📥 Descargar DNIs NO ENCONTRADOS (Excel)",
                        data=excel_no_encontrados,
                        file_name="resultado_no_encontrados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

            except Exception as e:
                st.error(f"Ocurrió un error: {e}")
    else:
        st.info("Sube ambos archivos para poder procesar la información.")


if __name__ == "__main__":
    run_app()
