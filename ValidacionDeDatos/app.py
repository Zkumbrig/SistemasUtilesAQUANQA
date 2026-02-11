import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import io
import re


def parse_horas_a_decimal(val):
    """
    Convierte un valor de horas a número decimal.
    Acepta: número (7.5), texto "HH:MM:SS" o "HH:MM", hora Excel, timedelta, datetime (solo tiempo).
    """
    if pd.isna(val) or val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        if val > 1 and val < 100:
            return float(val)
        if 0 <= val < 1:
            return float(val) * 24
        if 0 <= val < 24:
            return float(val)
        return float(val)
    if isinstance(val, timedelta):
        return val.total_seconds() / 3600.0
    if isinstance(val, (datetime, pd.Timestamp)):
        return val.hour + val.minute / 60.0 + val.second / 3600.0
    s = str(val).strip()
    if not s or s.lower() in ("nan", "nat", "none"):
        return 0.0
    n = pd.to_numeric(s, errors="coerce")
    if pd.notna(n):
        if 0 < n <= 24 and n != int(n):
            return float(n)
        if n > 24:
            return float(n)
        if 0 <= n < 1:
            return n * 24
        return float(n)
    m = re.match(r"^(\d{1,2})[:\.](\d{1,2})(?:[:\.](\d{1,2}))?", s)
    if m:
        h, m1, sec = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
        return h + m1 / 60.0 + sec / 3600.0
    return 0.0


def _setup_styles():
    # OJO: aquí NO hacemos st.set_page_config; eso lo maneja la app raíz.
    st.markdown(
        """
<style>
    /* Importar fuente */
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700&display=swap');
    
    /* Variables de tema */
    :root {
        --bg-primary: #0f172a;
        --bg-card: #1e293b;
        --bg-card-hover: #334155;
        --accent: #3b82f6;
        --accent-hover: #2563eb;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --text-primary: #f1f5f9;
        --text-muted: #94a3b8;
        --border: #334155;
        --radius: 12px;
        --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -2px rgba(0, 0, 0, 0.2);
    }
    
    /* Fondo y contenedor principal */
    .stApp {
        background: linear-gradient(165deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
        font-family: 'DM Sans', -apple-system, sans-serif;
    }
    
    /* Ocultar elementos por defecto de Streamlit */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* Hero / Header */
    .dashboard-header {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: var(--radius);
        padding: 2rem 2.5rem;
        margin-bottom: 2rem;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }
    .dashboard-header h1 {
        color: var(--text-primary);
        font-size: 2rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .dashboard-header p {
        color: var(--text-muted);
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    /* Tarjetas de métricas */
    .metric-card {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border-radius: var(--radius);
        padding: 1.25rem 1.5rem;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
        transition: transform 0.2s, border-color 0.2s;
    }
    .metric-card:hover {
        border-color: var(--accent);
        transform: translateY(-2px);
    }
    .metric-card .label {
        color: var(--text-muted);
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }
    .metric-card .value {
        color: var(--text-primary);
        font-size: 1.75rem;
        font-weight: 700;
    }
    .metric-card.success .value { color: var(--success); }
    .metric-card.warning .value { color: var(--warning); }
    .metric-card.danger .value { color: var(--danger); }
    
    /* Bloques de contenido */
    .content-block {
        background: #1e293b;
        border-radius: var(--radius);
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        border: 1px solid var(--border);
        box-shadow: var(--shadow);
    }
    .content-block h2, .content-block h3 {
        color: var(--text-primary);
        font-size: 1.15rem;
        font-weight: 600;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border);
    }
    
    /* Área de subida de archivo mejorada */
    .upload-section {
        background: linear-gradient(145deg, #1e293b 0%, #334155 100%);
        border: 2px dashed var(--border);
        border-radius: var(--radius);
        padding: 3rem 2rem;
        text-align: center;
        transition: border-color 0.2s, background 0.2s;
    }
    .upload-section:hover {
        border-color: var(--accent);
        background: linear-gradient(145deg, #334155 0%, #1e293b 100%);
    }
    
    /* Instrucciones en tarjetas */
    .instruction-card {
        background: #1e293b;
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin: 0.5rem 0;
        border-left: 4px solid var(--accent);
        color: var(--text-muted);
        font-size: 0.95rem;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-ok { background: rgba(16, 185, 129, 0.2); color: #10b981; }
    .badge-problem { background: rgba(239, 68, 68, 0.2); color: #ef4444; }
    .badge-warn { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
    
    /* Tabs personalizados (contexto visual) */
    .section-tabs {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1.5rem;
        flex-wrap: wrap;
    }
    
    /* Estilo para expanders */
    .streamlit-expanderHeader {
        background: #1e293b !important;
        border-radius: 8px !important;
    }
    
    /* DataFrames con fondo coherente */
    div[data-testid="stDataFrame"] {
        border-radius: var(--radius);
        overflow: hidden;
        border: 1px solid var(--border);
    }
</style>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
<div class="dashboard-header">
    <h1>📊 Validación de Asistencia y Horas</h1>
    <p>Analiza reportes de horas por persona, valida días laborados y detecta inconsistencias</p>
</div>
""",
        unsafe_allow_html=True,
    )


@st.cache_data
def load_excel(file):
    """Carga el archivo Excel y retorna el DataFrame"""
    try:
        df = pd.read_excel(file, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"Error al cargar el archivo: {str(e)}")
        return None

def detect_date_columns(df):
    """Detecta columnas que contienen fechas"""
    date_cols = []
    for col in df.columns:
        # Intentar convertir a fecha
        try:
            pd.to_datetime(df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None)
            date_cols.append(col)
        except:
            # Verificar si el nombre de la columna parece una fecha
            if any(keyword in str(col).lower() for keyword in ['fecha', 'date', 'dia', 'day']):
                date_cols.append(col)
    return date_cols

def detect_person_column(df):
    """Detecta la columna que contiene nombres de personas"""
    possible_names = ['nombre', 'persona', 'empleado', 'trabajador', 'name', 'employee']
    for col in df.columns:
        if any(name in str(col).lower() for name in possible_names):
            return col
    # Si no encuentra, usar la primera columna
    return df.columns[0]

def detect_hours_column(df):
    """Detecta columnas que contienen horas"""
    hours_cols = []
    for col in df.columns:
        if any(keyword in str(col).lower() for keyword in ['hora', 'hour', 'horas', 'tiempo', 'time']):
            hours_cols.append(col)
    return hours_cols

def process_data(df):
    """Procesa los datos del DataFrame"""
    # Detectar columnas importantes
    person_col = detect_person_column(df)
    date_cols = detect_date_columns(df)
    hours_cols = detect_hours_column(df)
    
    # Si no hay columnas de fecha detectadas, intentar usar todas las columnas numéricas excepto la de persona
    if not date_cols:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if person_col in numeric_cols:
            numeric_cols.remove(person_col)
        date_cols = numeric_cols[:10]  # Limitar a 10 columnas
    
    # Si no hay columnas de horas, usar todas las numéricas
    if not hours_cols:
        hours_cols = df.select_dtypes(include=['number']).columns.tolist()
        if person_col in hours_cols:
            hours_cols.remove(person_col)
    
    return person_col, date_cols, hours_cols

def calculate_statistics(df, person_col, date_cols, hours_cols, documento_col=None):
    """Calcula estadísticas por persona. Si una persona tiene varios cortes (filas), se suman las horas por fecha."""
    stats = []
    
    for person in df[person_col].unique():
        person_df = df[df[person_col] == person]
        
        grupo_col = None
        supervisor_col = None
        labor_col = None
        for col in df.columns:
            col_lower = str(col).lower()
            if 'grupo' in col_lower or 'codigo' in col_lower or 'código' in col_lower:
                grupo_col = col
            if 'supervisor' in col_lower:
                supervisor_col = col
            if 'labor' in col_lower or 'trabajo' in col_lower or 'actividad' in col_lower:
                labor_col = col
        
        documento = str(person_df[documento_col].iloc[0]) if documento_col and documento_col in person_df.columns else "N/A"
        grupo = person_df[grupo_col].iloc[0] if grupo_col and grupo_col in person_df.columns else "N/A"
        supervisor = person_df[supervisor_col].iloc[0] if supervisor_col and supervisor_col in person_df.columns else "N/A"
        labor = person_df[labor_col].iloc[0] if labor_col and labor_col in person_df.columns else "N/A"
        
        dias_laborados = []
        horas_por_fecha = {}
        total_horas = 0.0
        fechas_con_problemas = []
        
        for col in date_cols:
            if col not in person_df.columns:
                continue
            serie = person_df[col].apply(lambda x: pd.to_numeric(x, errors='coerce'))
            horas = float(serie.fillna(0).sum())
            if horas > 0:
                fecha_str = str(col)
                dias_laborados.append(fecha_str)
                horas_por_fecha[fecha_str] = round(horas, 2)
                total_horas += horas
                if horas < 9.58:
                    fechas_con_problemas.append(fecha_str)
        
        for col in hours_cols:
            if col not in date_cols and col in person_df.columns:
                total_horas += float(person_df[col].apply(lambda x: pd.to_numeric(x, errors='coerce')).fillna(0).sum())
        
        faltaron_dias = len(dias_laborados) < len(date_cols) if date_cols else False
        
        stats.append({
            'Persona': person,
            'Documento': documento,
            'Código de Grupo': grupo,
            'Supervisor': supervisor,
            'Labor': labor,
            'Días Laborados': len(dias_laborados),
            'Fechas Laboradas': ', '.join(dias_laborados) if dias_laborados else 'Ninguna',
            'Total Horas': round(total_horas, 2),
            'Horas por Fecha': horas_por_fecha,
            'Fechas con Problemas (< 9.58H)': fechas_con_problemas,
            'Faltaron Días': faltaron_dias,
            'Tiene Problemas': len(fechas_con_problemas) > 0 or faltaron_dias
        })
    
    return pd.DataFrame(stats)


def run_app():
    _setup_styles()

    # Interfaz principal
    col_upload, _ = st.columns([2, 1])
    with col_upload:
        uploaded_file = st.file_uploader(
            "📁 Sube el archivo Excel del reporte de horas",
            type=["xlsx", "xls"],
            help="Selecciona el archivo Excel que contiene el reporte de horas",
        )

    if uploaded_file is not None:
        df = load_excel(uploaded_file)

        if df is not None:
            st.markdown(
                f"""
        <div class="content-block" style="margin-bottom: 1rem;">
            <span style="color: #10b981;">✅ Archivo cargado</span> — 
            <strong>{len(df)}</strong> filas, <strong>{len(df.columns)}</strong> columnas
        </div>
        """,
                unsafe_allow_html=True,
            )

            # Vista previa en bloque con estilo
            with st.expander("👁️ Vista previa de los datos cargados", expanded=False):
                st.dataframe(df.head(10), use_container_width=True)
                st.caption(f"Columnas: {', '.join(df.columns.tolist())}")

            # Procesar datos
            person_col, date_cols, hours_cols = process_data(df)

            # Configuración en bloque visual
            st.markdown(
                '<div class="content-block"><h3>⚙️ Configuración de columnas</h3></div>',
                unsafe_allow_html=True,
            )
            col1, col2, col3 = st.columns(3)

            with col1:
                selected_person_col = st.selectbox(
                    "Columna de Personas/Nombres",
                    options=df.columns.tolist(),
                    index=df.columns.tolist().index(person_col) if person_col in df.columns else 0,
                )

            with col2:
                doc_options = ["Ninguna"] + [
                    col
                    for col in df.columns
                    if any(
                        k in str(col).lower()
                        for k in [
                            "documento",
                            "doc",
                            "dni",
                            "cedula",
                            "cédula",
                            "identificacion",
                            "identificación",
                            "ruc",
                            "nro doc",
                        ]
                    )
                ]
                default_doc = next(
                    (i for i, o in enumerate(doc_options) if o != "Ninguna" and "documento" in str(o).lower()),
                    0,
                )
                selected_documento_col = st.selectbox(
                    "Columna de Documento",
                    options=doc_options,
                    index=default_doc,
                )

            with col3:
                grupo_options = ["Ninguna"] + [
                    col
                    for col in df.columns
                    if "grupo" in str(col).lower()
                    or "codigo" in str(col).lower()
                    or "código" in str(col).lower()
                ]
                selected_grupo_col = st.selectbox(
                    "Columna de Código de Grupo",
                    options=grupo_options,
                    index=0,
                )

            col3b, col4, col5 = st.columns(3)
            with col3b:
                supervisor_options = ["Ninguna"] + [col for col in df.columns if "supervisor" in str(col).lower()]
                selected_supervisor_col = st.selectbox(
                    "Columna de Supervisor",
                    options=supervisor_options,
                    index=0,
                )

            with col5:
                labor_options = ["Ninguna"] + [
                    col
                    for col in df.columns
                    if any(k in str(col).lower() for k in ["labor", "trabajo", "actividad"])
                ]
                default_labor = labor_options.index("Actividad") if "Actividad" in labor_options else 0
                selected_labor_col = st.selectbox(
                    "Columna de Labor / Actividad",
                    options=labor_options,
                    index=default_labor,
                )

            st.caption(
                "Usa **Columna Fecha** y **Columna Total Horas** cuando cada fila es un registro de asistencia "
                "(fecha del día y horas de ese registro)."
            )
            col_fecha, col_total, col_dias = st.columns(3)
            with col_fecha:
                fecha_options = ["Ninguna"] + [
                    col
                    for col in df.columns
                    if any(k in str(col).lower() for k in ["fecha", "date", "dia", "día"])
                ]
                default_fecha = next(
                    (i for i, o in enumerate(fecha_options) if o != "Ninguna" and "fecha" in str(o).lower()),
                    0,
                )
                selected_fecha_col = st.selectbox(
                    "Columna Fecha (asistencia)",
                    options=fecha_options,
                    index=default_fecha,
                    help="Fecha en que ocurrió el registro. Cada fila puede ser un corte distinto.",
                )
            with col_total:
                total_horas_options = ["Ninguna"] + [
                    col
                    for col in df.columns
                    if any(k in str(col).lower() for k in ["total hora", "total horas", "horas", "total"])
                ]
                default_th = next(
                    (i for i, o in enumerate(total_horas_options) if o != "Ninguna" and "total" in str(o).lower()),
                    0,
                )
                selected_total_horas_col = st.selectbox(
                    "Columna Total Horas",
                    options=total_horas_options,
                    index=default_th,
                    help="Horas de ese registro. El total de la persona es la suma de todos sus registros.",
                )
            with col_dias:
                selected_date_cols = st.multiselect(
                    "O: columnas por día (alternativa)",
                    options=df.columns.tolist(),
                    default=[],
                    help="Solo si no usas Fecha + Total Horas: una columna por día con horas.",
                )

            usar_modo_fecha_total = selected_fecha_col != "Ninguna" and selected_total_horas_col != "Ninguna"

            if st.button("🔄 Procesar datos", type="primary"):
                if not usar_modo_fecha_total and not selected_date_cols:
                    st.warning(
                        "⚠️ Selecciona **Columna Fecha** y **Columna Total Horas**, o bien las columnas por día."
                    )
                else:
                    stats_list = []

                    for person in df[selected_person_col].unique():
                        person_df = df[df[selected_person_col] == person].copy()

                        documento = (
                            str(person_df[selected_documento_col].iloc[0])
                            if selected_documento_col != "Ninguna"
                            and selected_documento_col in person_df.columns
                            else "N/A"
                        )
                        grupo = (
                            person_df[selected_grupo_col].iloc[0]
                            if selected_grupo_col != "Ninguna" and selected_grupo_col in person_df.columns
                            else "N/A"
                        )
                        supervisor = (
                            person_df[selected_supervisor_col].iloc[0]
                            if selected_supervisor_col != "Ninguna" and selected_supervisor_col in person_df.columns
                            else "N/A"
                        )
                        labor = (
                            person_df[selected_labor_col].iloc[0]
                            if selected_labor_col != "Ninguna" and selected_labor_col in person_df.columns
                            else "N/A"
                        )

                        dias_laborados = []
                        horas_por_fecha = {}
                        total_horas = 0.0
                        fechas_con_problemas = []

                        if usar_modo_fecha_total:
                            f_col = selected_fecha_col
                            h_col = selected_total_horas_col
                            person_df["_horas_decimal"] = person_df[h_col].apply(parse_horas_a_decimal)
                            person_df = person_df[person_df["_horas_decimal"] > 0]
                            if len(person_df) == 0:
                                stats_list.append(
                                    {
                                        "Persona": person,
                                        "Documento": documento,
                                        "Código de Grupo": grupo,
                                        "Supervisor": supervisor,
                                        "Labor": labor,
                                        "Días Laborados": 0,
                                        "Fechas Laboradas": "Ninguna",
                                        "Total Horas": 0.0,
                                        "Horas por Fecha": {},
                                        "Fechas con Problemas (< 9.58H)": [],
                                        "Faltaron Días": False,
                                        "Tiene Problemas": True,
                                    }
                                )
                                continue
                            try:
                                dt = pd.to_datetime(person_df[f_col], errors="coerce", dayfirst=True)
                                person_df["_fecha_norm"] = dt.dt.strftime("%Y-%m-%d")
                                na_mask = person_df["_fecha_norm"].isna() | (person_df["_fecha_norm"] == "NaT")
                                if na_mask.any():
                                    person_df.loc[na_mask, "_fecha_norm"] = person_df.loc[na_mask, f_col].astype(str).str[:10]
                            except Exception:
                                person_df["_fecha_norm"] = person_df[f_col].astype(str).str[:10]
                            person_df = person_df[
                                person_df["_fecha_norm"].notna()
                                & (person_df["_fecha_norm"] != "NaT")
                                & (person_df["_fecha_norm"] != "nan")
                            ]
                            if len(person_df) == 0:
                                stats_list.append(
                                    {
                                        "Persona": person,
                                        "Documento": documento,
                                        "Código de Grupo": grupo,
                                        "Supervisor": supervisor,
                                        "Labor": labor,
                                        "Días Laborados": 0,
                                        "Fechas Laboradas": "Ninguna",
                                        "Total Horas": 0.0,
                                        "Horas por Fecha": {},
                                        "Fechas con Problemas (< 9.58H)": [],
                                        "Faltaron Días": False,
                                        "Tiene Problemas": True,
                                    }
                                )
                                continue
                            agrupado = person_df.groupby("_fecha_norm")["_horas_decimal"].sum()
                            for fecha_str, horas in agrupado.items():
                                horas = round(float(horas), 2)
                                dias_laborados.append(fecha_str)
                                horas_por_fecha[fecha_str] = horas
                                total_horas += horas
                                if horas < 9.58:
                                    fechas_con_problemas.append(fecha_str)
                            dias_laborados = sorted(dias_laborados)
                            total_horas = round(total_horas, 2)
                            faltaron_dias = False
                        else:
                            for col in selected_date_cols:
                                if col not in person_df.columns:
                                    continue
                                serie = person_df[col].apply(lambda x: pd.to_numeric(x, errors="coerce"))
                                horas = float(serie.fillna(0).sum())
                                if horas > 0:
                                    fecha_str = str(col)
                                    dias_laborados.append(fecha_str)
                                    horas_por_fecha[fecha_str] = round(horas, 2)
                                    total_horas += horas
                                    if horas < 9.58:
                                        fechas_con_problemas.append(fecha_str)
                            total_horas = round(total_horas, 2)
                            faltaron_dias = len(dias_laborados) < len(selected_date_cols)

                        stats_list.append(
                            {
                                "Persona": person,
                                "Documento": documento,
                                "Código de Grupo": grupo,
                                "Supervisor": supervisor,
                                "Labor": labor,
                                "Días Laborados": len(dias_laborados),
                                "Fechas Laboradas": ", ".join(dias_laborados) if dias_laborados else "Ninguna",
                                "Total Horas": total_horas,
                                "Horas por Fecha": horas_por_fecha,
                                "Fechas con Problemas (< 9.58H)": fechas_con_problemas,
                                "Faltaron Días": faltaron_dias,
                                "Tiene Problemas": len(fechas_con_problemas) > 0 or faltaron_dias,
                            }
                        )

                    stats_df = pd.DataFrame(stats_list)
                    st.session_state["stats_df"] = stats_df
                    st.session_state["selected_date_cols"] = selected_date_cols if not usar_modo_fecha_total else []
                    st.success("✅ Datos procesados exitosamente!")

            if "stats_df" in st.session_state:
                stats_df = st.session_state["stats_df"]
                _ = st.session_state.get("selected_date_cols", [])

                total_personas = len(stats_df)
                con_problemas = len(stats_df[stats_df["Tiene Problemas"] == True])
                faltaron_dias = len(stats_df[stats_df["Faltaron Días"] == True])
                horas_insuf = len(stats_df[stats_df["Fechas con Problemas (< 9.58H)"].apply(lambda x: len(x) > 0)])

                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                with kpi1:
                    st.markdown(
                        """
                <div class="metric-card">
                    <div class="label">Total personas</div>
                    <div class="value">{}</div>
                </div>
                """.format(total_personas),
                        unsafe_allow_html=True,
                    )
                with kpi2:
                    st.markdown(
                        """
                <div class="metric-card danger">
                    <div class="label">Con problemas</div>
                    <div class="value">{}</div>
                </div>
                """.format(con_problemas),
                        unsafe_allow_html=True,
                    )
                with kpi3:
                    st.markdown(
                        """
                <div class="metric-card warning">
                    <div class="label">Faltaron días</div>
                    <div class="value">{}</div>
                </div>
                """.format(faltaron_dias),
                        unsafe_allow_html=True,
                    )
                with kpi4:
                    st.markdown(
                        """
                <div class="metric-card warning">
                    <div class="label">Horas &lt; 9.58 en alguna fecha</div>
                    <div class="value">{}</div>
                </div>
                """.format(horas_insuf),
                        unsafe_allow_html=True,
                    )

                st.markdown('<div class="content-block"><h3>📈 Tabla de validación</h3>', unsafe_allow_html=True)

                with st.container():
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        mostrar_problemas = st.checkbox("🔴 Solo con problemas", value=False, key="f1")
                    with c2:
                        mostrar_faltaron = st.checkbox("⚠️ Solo que faltaron días", value=False, key="f2")
                    with c3:
                        mostrar_horas_insuficientes = st.checkbox("⏰ Solo horas < 9.58H", value=False, key="f3")
                    with c4:
                        st.caption(f"Mostrando: **{len(stats_df)}** personas")

                filtered_df = stats_df.copy()
                if mostrar_problemas:
                    filtered_df = filtered_df[filtered_df["Tiene Problemas"] == True]
                if mostrar_faltaron:
                    filtered_df = filtered_df[filtered_df["Faltaron Días"] == True]
                if mostrar_horas_insuficientes:
                    filtered_df = filtered_df[filtered_df["Fechas con Problemas (< 9.58H)"].apply(lambda x: len(x) > 0)]

                cols_tabla = ["Persona"]
                if "Documento" in filtered_df.columns:
                    cols_tabla.append("Documento")
                cols_tabla += ["Código de Grupo", "Supervisor", "Labor", "Días Laborados", "Total Horas", "Tiene Problemas"]
                display_df = filtered_df[[c for c in cols_tabla if c in filtered_df.columns]].copy()
                display_df["Estado"] = display_df["Tiene Problemas"].apply(lambda x: "🔴 Problemas" if x else "✅ OK")
                display_df = display_df.drop(columns=["Tiene Problemas"])

                def highlight_problems(row):
                    n = len(row)
                    s = "background-color: rgba(239, 68, 68, 0.2);" if row["Estado"] == "🔴 Problemas" else ""
                    return [s] * n

                st.dataframe(
                    display_df.style.apply(highlight_problems, axis=1),
                    use_container_width=True,
                    height=380,
                )
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown(
                    """
            <div class="content-block">
                <h3>🔍 Detalle por persona</h3>
            </div>
            """,
                    unsafe_allow_html=True,
                )

                sel_col, _ = st.columns([1, 2])
                with sel_col:
                    selected_person = st.selectbox(
                        "Selecciona una persona",
                        options=stats_df["Persona"].tolist(),
                        label_visibility="collapsed",
                    )

                person_data = stats_df[stats_df["Persona"] == selected_person].iloc[0]
                problemas_count = len(person_data["Fechas con Problemas (< 9.58H)"])

                m1, m2, m3, m4 = st.columns(4)
                with m1:
                    st.markdown(
                        """
                <div class="metric-card">
                    <div class="label">Días laborados</div>
                    <div class="value">{}</div>
                </div>
                """.format(person_data["Días Laborados"]),
                        unsafe_allow_html=True,
                    )
                with m2:
                    st.markdown(
                        """
                <div class="metric-card success">
                    <div class="label">Total horas</div>
                    <div class="value">{}h</div>
                </div>
                """.format(person_data["Total Horas"]),
                        unsafe_allow_html=True,
                    )
                with m3:
                    st.markdown(
                        """
                <div class="metric-card {}">
                    <div class="label">Fechas con &lt; 9.58h</div>
                    <div class="value">{}</div>
                </div>
                """.format("danger" if problemas_count > 0 else "", problemas_count),
                        unsafe_allow_html=True,
                    )
                with m4:
                    st.markdown(
                        """
                <div class="metric-card {}">
                    <div class="label">Faltaron días</div>
                    <div class="value">{}</div>
                </div>
                """.format("danger" if person_data["Faltaron Días"] else "success", "Sí" if person_data["Faltaron Días"] else "No"),
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    """
            <div class="content-block" style="padding: 1rem 1.5rem;">
                <p style="color: #94a3b8; margin: 0; font-size: 0.9rem;">
                    <strong style="color: #f1f5f9;">Documento:</strong> {} &nbsp;|&nbsp;
                    <strong style="color: #f1f5f9;">Código de grupo:</strong> {} &nbsp;|&nbsp;
                    <strong style="color: #f1f5f9;">Supervisor:</strong> {} &nbsp;|&nbsp;
                    <strong style="color: #f1f5f9;">Labor / Actividad:</strong> {}
                </p>
                <p style="color: #94a3b8; margin: 0.5rem 0 0 0; font-size: 0.85rem;">
                    Fechas laboradas: {}
                </p>
            </div>
            """.format(
                        person_data.get("Documento", "N/A"),
                        person_data["Código de Grupo"],
                        person_data["Supervisor"],
                        person_data["Labor"],
                        person_data["Fechas Laboradas"] or "Ninguna",
                    ),
                    unsafe_allow_html=True,
                )

                st.markdown('<div class="content-block"><h3>⏱️ Horas por fecha</h3>', unsafe_allow_html=True)
                horas_dict = person_data["Horas por Fecha"]
                if horas_dict:
                    horas_df = pd.DataFrame(
                        [
                            {"Fecha": fecha, "Horas": horas, "Estado": "⚠️ < 9.58h" if horas < 9.58 else "✅ OK"}
                            for fecha, horas in horas_dict.items()
                        ]
                    )

                    def color_hours(val):
                        if val < 9.58:
                            return "background-color: rgba(239, 68, 68, 0.25);"
                        return "background-color: rgba(16, 185, 129, 0.2);"

                    try:
                        styled = horas_df.style.map(color_hours, subset=["Horas"])
                    except AttributeError:
                        styled = horas_df.style.applymap(color_hours, subset=["Horas"])
                    st.dataframe(styled, use_container_width=True)

                    fig = go.Figure()
                    colors = ["#ef4444" if h < 9.58 else "#10b981" for h in horas_df["Horas"]]
                    fig.add_trace(
                        go.Bar(
                            x=horas_df["Fecha"],
                            y=horas_df["Horas"],
                            text=horas_df["Horas"].round(1),
                            textposition="outside",
                            marker_color=colors,
                            name="Horas",
                        )
                    )
                    fig.add_hline(y=9.58, line_dash="dash", line_color="#f59e0b", annotation_text="Mín. 9.58h")
                    fig.update_layout(
                        template="plotly_dark",
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(30, 41, 59, 0.5)",
                        font=dict(color="#f1f5f9", size=12),
                        title=dict(text=f"Horas por fecha — {selected_person}", font=dict(size=16)),
                        height=380,
                        margin=dict(t=50, b=60),
                        xaxis=dict(tickangle=-45),
                        showlegend=False,
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("No se encontraron horas registradas para esta persona.")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown(
                    """
            <div class="content-block">
                <h3>💾 Exportar resultados</h3>
            </div>
            """,
                    unsafe_allow_html=True,
                )

                export_df = stats_df.copy()
                export_df["Fechas con Problemas"] = export_df["Fechas con Problemas (< 9.58H)"].apply(
                    lambda x: ", ".join(x) if x else "Ninguna"
                )
                export_df = export_df.drop(columns=["Horas por Fecha", "Fechas con Problemas (< 9.58H)"])
                if "Documento" not in export_df.columns:
                    export_df.insert(1, "Documento", "N/A")

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine="openpyxl") as writer:
                    export_df.to_excel(writer, index=False, sheet_name="Validación")

                st.download_button(
                    label="📥 Descargar validación en Excel",
                    data=output.getvalue(),
                    file_name=f"validacion_asistencia_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )

    else:
        st.markdown(
            """
    <div class="upload-section">
        <p style="color: #94a3b8; font-size: 1.1rem; margin-bottom: 0.5rem;">Sube tu archivo Excel arriba para comenzar</p>
        <p style="color: #64748b; font-size: 0.9rem;">Formatos soportados: .xlsx, .xls</p>
    </div>
    """,
            unsafe_allow_html=True,
        )

        st.markdown(
            "<h3 style='color: #f1f5f9; font-size: 1.1rem; margin-top: 2rem;'>📋 Cómo usar</h3>",
            unsafe_allow_html=True,
        )
        st.markdown(
            """
    <div class="instruction-card">1. Sube el archivo Excel con el reporte de horas.</div>
    <div class="instruction-card">2. Configura las columnas: personas, documento, grupo, supervisor, labor. Usa <strong>Columna Fecha</strong> (asistencia) y <strong>Columna Total Horas</strong> si cada fila es un registro.</div>
    <div class="instruction-card">3. Haz clic en <strong>Procesar datos</strong> para analizar.</div>
    <div class="instruction-card">4. Revisa las tarjetas de resumen y la tabla; usa los filtros para ver solo personas con problemas.</div>
    <div class="instruction-card">5. Selecciona una persona para ver detalle de horas por fecha y el gráfico.</div>
    <div class="instruction-card">6. Exporta los resultados en Excel si lo necesitas.</div>
    """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    run_app()

