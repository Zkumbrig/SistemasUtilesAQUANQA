import streamlit as st

# Importamos las apps como módulos
from ValidacionQbiz import app as app_qbiz
from BajaPersonalDatos import app as app_baja_personal
from ValidacionDeDatos import app as app_validacion_avanzada


def main():
    st.set_page_config(
        page_title="AquAnqa Utilities",
        page_icon="📂",
        layout="wide",
    )

    st.sidebar.title("AquAnqa Utilities")
    opcion = st.sidebar.radio(
        "Elige una herramienta:",
        (
            "Validación simple de asistencia (Qbiz)",
            "Validación avanzada de asistencia y horas",
            "Filtro de DNIs contra data global",
        ),
    )

    if opcion == "Validación simple de asistencia (Qbiz)":
        app_qbiz.run_app()
    elif opcion == "Validación avanzada de asistencia y horas":
        app_validacion_avanzada.run_app()
    elif opcion == "Filtro de DNIs contra data global":
        app_baja_personal.run_app()


if __name__ == "__main__":
    main()


