"""
Aplicación de validación de datos de asistencia.
Carga archivo Excel (.xlsx) y detecta duplicados por DNI y nombres vacíos.
"""

import io
import streamlit as st
import pandas as pd


def run_app():
    st.title("📋 Validación de datos de asistencia")
    st.markdown("Carga un archivo Excel (.xlsx) para validar duplicados por DNI y nombres vacíos.")

    uploaded_file = st.file_uploader(
        "Selecciona un archivo Excel",
        type=["xlsx"],
        help="Solo se aceptan archivos .xlsx",
    )

    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file, engine="openpyxl")
        except Exception as e:
            st.error(f"Error al leer el archivo: {e}")
            st.stop()

        if df.empty:
            st.warning("El archivo está vacío.")
            st.stop()

        # Normalizar nombres de columnas (por si vienen con espacios o mayúsculas)
        df.columns = df.columns.str.strip()

        has_duplicates = False
        has_empty_names = False

        # --- Lógica de duplicados (solo columna DNI) ---
        if "DNI" not in df.columns:
            st.error("El archivo debe contener una columna 'DNI'.")
            st.stop()

        duplicated_mask = df.duplicated(subset=["DNI"], keep=False)
        duplicates_df = df.loc[duplicated_mask]

        # Columnas de justificación (sin Hr Entrada/Salida al menos una debe ser 1)
        JUSTIFICACION_COLS = ["D.Ausencia", "D.Permiso", "D.Permiso Goce", "D.Vacaciones", "D.Licencia"]
        justificacion_en_df = [c for c in JUSTIFICACION_COLS if c in df.columns]

        # Columnas a mostrar para duplicados: DNI, Nombre, Hr Entrada, Hr Salida + "Con valor 1 en" (solo filas con DNI repetido 2+ veces)
        dup_columns = ["DNI", "Nombre", "Hr Entrada", "Hr Salida"]
        available_dup_cols = [c for c in dup_columns if c in df.columns]
        if not available_dup_cols:
            available_dup_cols = list(df.columns)

        dup_display = duplicates_df[available_dup_cols].copy() if available_dup_cols else duplicates_df

        # Añadir columna "Con valor 1 en" para saber en qué justificación tiene 1 (solo en la tabla de duplicados)
        if justificacion_en_df and not dup_display.empty:
            dup_display = dup_display.copy()
            dup_display["Con valor 1 en"] = dup_display.apply(
                lambda r: ", ".join(
                    [c for c in justificacion_en_df if pd.notna(df.loc[r.name, c]) and str(df.loc[r.name, c]).strip() == "1"]
                )
                or "—",
                axis=1,
            )

        if not dup_display.empty:
            has_duplicates = True
            st.subheader("⚠️ Registros duplicados (por DNI)")
            st.dataframe(dup_display, use_container_width=True)

            # Opción de descarga para duplicados
            buffer_dup = io.BytesIO()
            dup_display.to_excel(buffer_dup, index=False, engine="openpyxl")
            buffer_dup.seek(0)
            st.download_button(
                label="📥 Descargar duplicados (Excel)",
                data=buffer_dup,
                file_name="duplicados_asistencia.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_duplicates",
            )

        # --- Lógica de nombres vacíos ---
        if "Nombre" not in df.columns:
            st.warning("No se encontró la columna 'Nombre'. Se omite la validación de nombres vacíos.")
        else:
            empty_name_mask = df["Nombre"].isna() | (df["Nombre"].astype(str).str.strip() == "")
            empty_names_df = df.loc[empty_name_mask]

            if not empty_names_df.empty:
                has_empty_names = True
                st.subheader("⚠️ Registros con Nombre vacío o nulo")
                st.dataframe(empty_names_df, use_container_width=True)

                buffer_empty = io.BytesIO()
                empty_names_df.to_excel(buffer_empty, index=False, engine="openpyxl")
                buffer_empty.seek(0)
                st.download_button(
                    label="📥 Descargar registros con nombre vacío (Excel)",
                    data=buffer_empty,
                    file_name="nombres_vacios_asistencia.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_empty_names",
                )

        # --- Sin Hr Entrada ni Hr Salida: al menos una de D.Ausencia, D.Permiso, etc. debe ser 1 ---
        has_sin_justificacion = False
        hr_entrada_col = "Hr Entrada" if "Hr Entrada" in df.columns else None
        hr_salida_col = "Hr Salida" if "Hr Salida" in df.columns else None
        if hr_entrada_col is not None and hr_salida_col is not None and justificacion_en_df:
            def esta_vacio(val):
                if pd.isna(val):
                    return True
                s = str(val).strip()
                return s == "" or s.lower() in ("nan", "none")

            sin_entrada_ni_salida = df.apply(
                lambda r: esta_vacio(r[hr_entrada_col]) and esta_vacio(r[hr_salida_col]),
                axis=1,
            )
            filas_sin_horas = df.loc[sin_entrada_ni_salida]

            def alguna_justificacion_es_1(row):
                for c in justificacion_en_df:
                    v = row.get(c)
                    if pd.notna(v) and str(v).strip() == "1":
                        return True
                return False

            filas_sin_justificacion = filas_sin_horas.loc[~filas_sin_horas.apply(alguna_justificacion_es_1, axis=1)]

            if not filas_sin_justificacion.empty:
                has_sin_justificacion = True
                cols_mostrar = [c for c in ["DNI", "Nombre", "Hr Entrada", "Hr Salida"] + justificacion_en_df if c in df.columns]
                reporte_sin_just = filas_sin_justificacion[cols_mostrar].copy()
                reporte_sin_just["Con valor 1 en"] = "— (ninguna tiene 1)"
                st.subheader("⚠️ Sin Hr. Entrada ni Hr. Salida y ninguna justificación en 1")
                st.markdown(
                    "Estos registros tienen **Hr. Entrada** y **Hr. Salida** vacías y **ninguna** de "
                    "D.Ausencia, D.Permiso, D.Permiso Goce, D.Vacaciones, D.Licencia tiene valor 1."
                )
                st.dataframe(reporte_sin_just, use_container_width=True)
                buffer_sin = io.BytesIO()
                reporte_sin_just.to_excel(buffer_sin, index=False, engine="openpyxl")
                buffer_sin.seek(0)
                st.download_button(
                    label="📥 Descargar sin justificación (Excel)",
                    data=buffer_sin,
                    file_name="sin_justificacion_asistencia.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_sin_justificacion",
                )
        elif hr_entrada_col and hr_salida_col and not justificacion_en_df:
            st.warning(
                "No se encontraron las columnas D.Ausencia, D.Permiso, D.Permiso Goce, "
                "D.Vacaciones o D.Licencia. No se valida justificación cuando faltan horas."
            )

        # --- Mensaje de éxito si no hay errores ---
        if not has_duplicates and not has_empty_names and not has_sin_justificacion:
            st.success("✅ Archivo limpio: No se encontraron errores.")

    else:
        st.info("Sube un archivo .xlsx para comenzar la validación.")


if __name__ == "__main__":
    run_app()

