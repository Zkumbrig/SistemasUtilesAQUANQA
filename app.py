import streamlit as st

# Importamos las apps como módulos
from ValidacionQbiz import app as app_qbiz
from BajaPersonalDatos import app as app_baja_personal
from ValidacionDeDatos import app as app_validacion_avanzada


SIDEBAR_CSS = """
<style>
    /* Fondo global */
    .stApp {
        background: linear-gradient(165deg, #0f172a 0%, #1e293b 40%, #0f172a 100%);
    }
    /* Sidebar contenedor */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        border-right: 1px solid rgba(51, 65, 85, 0.8);
    }
    [data-testid="stSidebar"] > div:first-child {
        padding-top: 0.5rem;
    }
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.5rem;
    }
    [data-testid="stSidebar"] .stRadio label {
        padding: 0.6rem 0.9rem !important;
        border-radius: 10px !important;
        background: rgba(30, 41, 59, 0.7) !important;
        border: 1px solid rgba(51, 65, 85, 0.6) !important;
        color: #cbd5e1 !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        background: rgba(51, 65, 85, 0.9) !important;
        border-color: #3b82f6 !important;
    }
    [data-testid="stSidebar"] .stRadio label span {
        color: inherit !important;
    }
</style>
"""


def render_sidebar():
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(
            """
            <div style="
                padding: 1.25rem 0 1rem 0;
                border-bottom: 1px solid rgba(51, 65, 85, 0.6);
                margin-bottom: 1.25rem;
            ">
                <p style="
                    margin: 0;
                    font-size: 1.35rem;
                    font-weight: 700;
                    color: #f1f5f9;
                    letter-spacing: -0.02em;
                ">📂 AquAnqa Utilities</p>
                <p style="margin: 0.35rem 0 0 0; font-size: 0.8rem; color: #94a3b8;">
                    Herramientas de validación y datos
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em;">Elige una herramienta</p>',
            unsafe_allow_html=True,
        )

        opcion = st.radio(
            "Herramienta",
            (
                "Validación simple de asistencia (Qbiz)",
                "Validación de CECO y Actividad",
                "Filtro de DNIs contra data global",
            ),
            label_visibility="collapsed",
        )

        st.markdown(
            """
            <div style="
                margin-top: 2rem;
                padding-top: 1rem;
                border-top: 1px solid rgba(51, 65, 85, 0.5);
                font-size: 0.75rem;
                color: #64748b;
                text-align: center;
            ">AquAnqa Utilities</div>
            """,
            unsafe_allow_html=True,
        )
    return opcion


def main():
    st.set_page_config(
        page_title="AquAnqa Utilities",
        page_icon="📂",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    opcion = render_sidebar()

    if opcion == "Validación simple de asistencia (Qbiz)":
        app_qbiz.run_app()
    elif opcion == "Validación de CECO y Actividad":
        app_validacion_avanzada.run_app()
    elif opcion == "Filtro de DNIs contra data global":
        app_baja_personal.run_app()


if __name__ == "__main__":
    main()


