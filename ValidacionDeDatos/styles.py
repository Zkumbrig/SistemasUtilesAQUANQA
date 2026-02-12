import streamlit as st


def setup_styles() -> None:
    st.markdown(
        """
<style>
    :root {
        --bg-primary: #0f172a;
        --bg-card: #1e293b;
        --text-primary: #f1f5f9;
        --text-muted: #94a3b8;
        --accent: #3b82f6;
        --danger: #ef4444;
        --warning: #f59e0b;
        --success: #10b981;
        --border: #334155;
    }

    .stApp {
        background: linear-gradient(165deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
    }

    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }

    .vd-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.25rem;
    }

    .vd-header h1 {
        color: var(--text-primary);
        margin: 0;
        font-size: 1.7rem;
    }

    .vd-header p {
        color: var(--text-muted);
        margin: 0.4rem 0 0;
        font-size: 0.95rem;
    }

    .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1rem 1.2rem;
    }

    .metric-label {
        color: var(--text-muted);
        font-size: 0.78rem;
        text-transform: uppercase;
    }

    .metric-value {
        color: var(--text-primary);
        font-size: 1.5rem;
        font-weight: 700;
    }

    .metric-danger .metric-value { color: var(--danger); }
    .metric-warning .metric-value { color: var(--warning); }
    .metric-success .metric-value { color: var(--success); }

    .vd-section {
        margin-top: 1rem;
        margin-bottom: 0.6rem;
        padding: 0.7rem 0.9rem;
        border: 1px solid var(--border);
        border-radius: 10px;
        background: rgba(30, 41, 59, 0.55);
    }

    .vd-section .title {
        color: var(--text-primary);
        font-weight: 600;
        font-size: 1rem;
        margin: 0;
    }

    .vd-section .subtitle {
        color: var(--text-muted);
        margin: 0.2rem 0 0 0;
        font-size: 0.86rem;
    }

    .vd-help {
        color: var(--text-muted);
        font-size: 0.83rem;
        margin-top: 0.2rem;
    }
</style>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="vd-header">
    <h1>Validacion de CECO y Actividad por Persona</h1>
    <p>Analiza un archivo de una misma fecha y detecta inconsistencias de CECO/Actividad por persona.</p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_metric(label: str, value: int | str, tone: str = "") -> None:
    tone_class = f"metric-{tone}" if tone else ""
    st.markdown(
        f"""
<div class="metric-card {tone_class}">
    <div class="metric-label">{label}</div>
    <div class="metric-value">{value}</div>
</div>
""",
        unsafe_allow_html=True,
    )
