import streamlit as st
import pandas as pd
from io import BytesIO

def inferir_genero_por_nombre(nombre: str, diccionario: dict | None = None) -> str:
    """
    Intenta asignar un sexo (M/F) según el primer nombre.
    Esto es solo una heurística simple, no es perfecto.
    """
    if not isinstance(nombre, str) or not nombre.strip():
        return "N"  # No determinado

    # Tomamos solo el primer nombre
    primer_nombre = nombre.strip().split()[0].upper()

    # 1) Si tenemos diccionario externo, lo usamos primero
    if diccionario:
        sexo_dic = diccionario.get(primer_nombre)
        if isinstance(sexo_dic, str) and sexo_dic.strip():
            return sexo_dic.strip().upper()

    # Algunos nombres comunes definidos manualmente
    nombres_f = {
        "MARICIELO", "MARIA", "ANA", "LUISA", "KAREN", "SOFIA", "CARLA", "ROCIO",
        "PATRICIA", "ELIZABETH", "JULIETA", "ANDREA", "CLAUDIA"
    }
    nombres_m = {
        "JUAN", "CARLOS", "LUIS", "PEDRO", "JORGE", "MIGUEL", "JOSE", "ALBERTO",
        "RICARDO", "ANDRES", "DIEGO", "OSCAR", "RAUL"
    }

    if primer_nombre in nombres_f:
        return "F"
    if primer_nombre in nombres_m:
        return "M"

    # Regla general muy simple: termina en A -> F, en otro caso -> M
    if primer_nombre.endswith("A"):
        return "F"
    return "M"

def procesar_archivos(archivo_global, archivo_filtro, archivo_diccionario=None):
    # Leer Excels
    df_global = pd.read_excel(archivo_global, dtype=str)
    df_filtro = pd.read_excel(archivo_filtro, dtype=str)

    # Cargar diccionario de nombres si se proporcionó
    diccionario_nombres = {}
    if archivo_diccionario is not None:
        df_dic = pd.read_excel(archivo_diccionario, dtype=str)
        if "NOMBRE" not in df_dic.columns or "SEXO" not in df_dic.columns:
            raise ValueError(
                "El diccionario debe tener las columnas 'NOMBRE' y 'SEXO'. "
                f"Columnas encontradas: {list(df_dic.columns)}"
            )
        df_dic["NOMBRE"] = df_dic["NOMBRE"].astype(str).str.strip().str.upper()
        df_dic["SEXO"] = df_dic["SEXO"].astype(str).str.strip().str.upper()
        diccionario_nombres = dict(zip(df_dic["NOMBRE"], df_dic["SEXO"]))

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

    # Normalizar
    df_global[col_global] = df_global[col_global].astype(str).str.strip()
    df_filtro[col_filtro] = df_filtro[col_filtro].astype(str).str.strip()

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

    # Intentar detectar automáticamente la columna de nombre
    # Buscamos la primera columna que contenga "NOMBRE" o "NOMBRES"
    col_nombre = None
    for col in df_encontrados.columns:
        col_mayus = str(col).upper()
        if "NOMBRE" in col_mayus:
            col_nombre = col
            break

    # Si encontramos una columna de nombre, calculamos sexo inferido
    if col_nombre is not None:
        df_encontrados["SEXO_INFERIDO"] = df_encontrados[col_nombre].apply(
            lambda x: inferir_genero_por_nombre(x, diccionario_nombres)
        )

    # Eliminamos columnas auxiliares para que la data quede "limpia"
    df_encontrados = df_encontrados.drop(columns=["_merge", "DNI_MERGE"])

    # No encontrados
    df_no_encontrados = (
        df_merge[df_merge["_merge"] == "left_only"][["DNI_MERGE"]]
        .drop_duplicates()
        .rename(columns={"DNI_MERGE": col_filtro})
    )
    df_no_encontrados["MENSAJE"] = "DNI no se encontró en la data global"

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
    archivo_diccionario = st.file_uploader(
        "Opcional: sube un Excel de DICCIONARIO DE NOMBRES (columnas 'NOMBRE' y 'SEXO')",
        type=["xlsx"],
        key="diccionario",
    )

    if archivo_global is not None and archivo_filtro is not None:
        if st.button("Procesar archivos"):
            try:
                df_encontrados, df_no_encontrados = procesar_archivos(
                    archivo_global, archivo_filtro, archivo_diccionario
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
