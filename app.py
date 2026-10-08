import streamlit as st
import pandas as pd
import plotly.express as px
import io

# Configuración Inicial
st.set_page_config(
    page_title="Dashboard Gerencial de Ausentismo Laboral", 
    layout="wide",
    page_icon="🏥"
)

# Encabezado principal
st.title("🏥 Dashboard Gerencial de Gestión de Ausentismo Laboral")
st.caption("Panel de Control para Dirección Ejecutiva y Gestión Humana | Base 3FN (2026)")

# 1. SECCIÓN DE CARGA DE ARCHIVO
st.header("1. Cargar Archivo de Ausentismo")
col_upload, col_info = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader("Seleccione el archivo Excel de Ausentismo (.xlsx)", type=["xlsx", "xls"])

with col_info:
    with st.expander("Estructura Requerida (3FN)", expanded=True):
        st.write("El archivo Excel debe contener las hojas:")
        st.code("""AUSENTISMO (Transaccional)\nEMPLEADO\nPUESTO_TRABAJO\nGRUPO\nTIPO_AUSENTISMO\nDIAGNOSTICO_MEDICO\nENTIDAD_SALUD""", language="text")

# Procesamiento de datos si se carga un archivo
if uploaded_file is not None:
    try:
        xls = pd.ExcelFile(uploaded_file)
        
        # Cargar cada hoja
        df_aus = pd.read_excel(xls, sheet_name='AUSENTISMO (Transaccional)')
        df_emp = pd.read_excel(xls, sheet_name='EMPLEADO')
        df_puesto = pd.read_excel(xls, sheet_name='PUESTO_TRABAJO')
        df_grupo = pd.read_excel(xls, sheet_name='GRUPO')
        df_tipo = pd.read_excel(xls, sheet_name='TIPO_AUSENTISMO')
        df_diag = pd.read_excel(xls, sheet_name='DIAGNOSTICO_MEDICO')
        df_entidad = pd.read_excel(xls, sheet_name='ENTIDAD_SALUD')

        # Convertir fechas a datetime
        if 'inicio_ausentismo' in df_aus.columns:
            df_aus['inicio_ausentismo'] = pd.to_datetime(df_aus['inicio_ausentismo'], dayfirst=True, errors='coerce')
        if 'final_ausentismo' in df_aus.columns:
            df_aus['final_ausentismo'] = pd.to_datetime(df_aus['final_ausentismo'], dayfirst=True, errors='coerce')

        # Relacionar las tablas (Merge / JOIN)
        df = df_aus.merge(df_emp, on='id_empleado', how='left')
        df = df.merge(df_puesto, on='id_puesto', how='left')
        df = df.merge(df_grupo, on='id_grupo', how='left')
        df = df.merge(df_tipo, on='id_tipo_ausentismo', how='left')
        df = df.merge(df_diag, on='id_diagnostico', how='left')
        df = df.merge(df_entidad, on='id_entidad', how='left')

        # Rellenar valores nulos en columnas clave de filtrado para evitar perdidas al filtrar
        if 'nombre_entidad' in df.columns:
            df['nombre_entidad'] = df['nombre_entidad'].fillna("SIN ENTIDAD / NO APLICA")
        if 'agencia' in df.columns:
            df['agencia'] = df['agencia'].fillna("SIN AGENCIA")
        if 'desc_tipo_ausentismo' in df.columns:
            df['desc_tipo_ausentismo'] = df['desc_tipo_ausentismo'].fillna("NO ESPECIFICADO")
        if 'cargo' in df.columns:
            df['cargo'] = df['cargo'].fillna("NO ESPECIFICADO")
        if 'nombre_grupo' in df.columns:
            df['nombre_grupo'] = df['nombre_grupo'].fillna("SIN GRUPO")
        if 'desc_diagnostico' in df.columns:
            df['desc_diagnostico'] = df['desc_diagnostico'].fillna("SIN DIAGNÓSTICO")

        st.success("✅ Base de datos cargada e integrada correctamente.")
    except Exception as e:
        st.error(f"Error al integrar las hojas del archivo: {e}")
        st.stop()
else:
    st.info("💡 Cargue el archivo 'Base_Datos_Ausentismo_Normalizada_3FN.xlsx' para activar el dashboard.")
    st.stop()

# 2. BARRA LATERAL (CONTROL CENTER - FILTROS Y SIMULADOR)
st.sidebar.header("🎛️ Control Center - Filtros")

def init_checkbox_keys(key_prefix, options):
    for opt in options:
        k = f"{key_prefix}_{opt}"
        if k not in st.session_state:
            st.session_state[k] = True

def set_all_keys(key_prefix, options, value):
    for opt in options:
        st.session_state[f"{key_prefix}_{opt}"] = value

# --- FILTRO POR RANGO DE FECHAS ---
if 'inicio_ausentismo' in df.columns and df['inicio_ausentismo'].notna().any():
    min_date = df['inicio_ausentismo'].min().date()
    max_date = df['inicio_ausentismo'].max().date()
    
    with st.sidebar.expander("📅 Rango de Fechas", expanded=True):
        rango_fechas = st.date_input(
            "Seleccionar Período (Inicio - Fin)",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
else:
    rango_fechas = None

# --- FILTRO POR AGENCIA ---
agencias_opt = sorted(df['agencia'].astype(str).unique().tolist()) if 'agencia' in df.columns else []
init_checkbox_keys("ag", agencias_opt)
agencias_sel = []

with st.sidebar.expander("🏢 Agencia / Sede", expanded=False):
    col_ag1, col_ag2 = st.columns(2)
    if col_ag1.button("✅ Todos", key="btn_all_ag"):
        set_all_keys("ag", agencias_opt, True)
    if col_ag2.button("❌ Ninguno", key="btn_none_ag"):
        set_all_keys("ag", agencias_opt, False)
        
    for ag in agencias_opt:
        if st.checkbox(str(ag), key=f"ag_{ag}"):
            agencias_sel.append(ag)

# --- FILTRO POR TIPO DE AUSENTISMO ---
tipos_opt = sorted(df['desc_tipo_ausentismo'].astype(str).unique().tolist()) if 'desc_tipo_ausentismo' in df.columns else []
init_checkbox_keys("t", tipos_opt)
tipos_sel = []

with st.sidebar.expander("🩺 Tipo de Ausentismo", expanded=False):
    col_t1, col_t2 = st.columns(2)
    if col_t1.button("✅ Todos", key="btn_all_t"):
        set_all_keys("t", tipos_opt, True)
    if col_t2.button("❌ Ninguno", key="btn_none_t"):
        set_all_keys("t", tipos_opt, False)
        
    for t in tipos_opt:
        if st.checkbox(str(t), key=f"t_{t}"):
            tipos_sel.append(t)

# --- FILTRO POR ENTIDAD DE SALUD (EPS / ARL) ---
entidades_opt = sorted(df['nombre_entidad'].astype(str).unique().tolist()) if 'nombre_entidad' in df.columns else []
init_checkbox_keys("ent", entidades_opt)
entidades_sel = []

with st.sidebar.expander("🏥 Entidad de Salud (EPS / ARL)", expanded=False):
    col_e1, col_e2 = st.columns(2)
    if col_e1.button("✅ Todos", key="btn_all_ent"):
        set_all_keys("ent", entidades_opt, True)
    if col_e2.button("❌ Ninguno", key="btn_none_ent"):
        set_all_keys("ent", entidades_opt, False)
        
    for ent in entidades_opt:
        if st.checkbox(str(ent), key=f"ent_{ent}"):
            entidades_sel.append(ent)

# --- FILTRO POR CARGO ---
cargos_opt = sorted(df['cargo'].astype(str).unique().tolist()) if 'cargo' in df.columns else []
init_checkbox_keys("c", cargos_opt)
cargos_sel = []

with st.sidebar.expander("💼 Cargo", expanded=False):
    col_c1, col_c2 = st.columns(2)
    if col_c1.button("✅ Todos", key="btn_all_c"):
        set_all_keys("c", cargos_opt, True)
    if col_c2.button("❌ Ninguno", key="btn_none_c"):
        set_all_keys("c", cargos_opt, False)
        
    for c in cargos_opt:
        if st.checkbox(str(c), key=f"c_{c}"):
            cargos_sel.append(c)

# --- BUSCADOR LIBRE ---
busqueda_emp = st.sidebar.text_input("🔍 Buscar Empleado por nombre o ID")

# --- SIMULADOR GERENCIAL DE COSTO DIA ---
st.sidebar.markdown("---")
st.sidebar.subheader("💰 Estimación Económica")
costo_dia_prom = st.sidebar.number_input("Costo promedio Día/Hombre ($)", value=80000, step=5000)

# APLICAR FILTROS
df_filtrado = df.copy()

if rango_fechas and len(rango_fechas) == 2:
    fecha_ini, fecha_fin = rango_fechas
    df_filtrado = df_filtrado[
        (df_filtrado['inicio_ausentismo'].dt.date >= fecha_ini) &
        (df_filtrado['inicio_ausentismo'].dt.date <= fecha_fin)
    ]

if agencias_opt:
    df_filtrado = df_filtrado[df_filtrado['agencia'].astype(str).isin(agencias_sel)]
if tipos_opt:
    df_filtrado = df_filtrado[df_filtrado['desc_tipo_ausentismo'].astype(str).isin(tipos_sel)]
if entidades_opt:
    df_filtrado = df_filtrado[df_filtrado['nombre_entidad'].astype(str).isin(entidades_sel)]
if cargos_opt:
    df_filtrado = df_filtrado[df_filtrado['cargo'].astype(str).isin(cargos_sel)]

if busqueda_emp:
    df_filtrado = df_filtrado[
        df_filtrado['nombre_completo'].astype(str).str.contains(busqueda_emp, case=False, na=False) |
        df_filtrado['id_empleado'].astype(str).str.contains(busqueda_emp, case=False, na=False)
    ]

st.sidebar.metric("Registros Filtrados", f"{len(df_filtrado):,} de {len(df):,}")

if df_filtrado.empty:
    st.warning("No hay datos disponibles para la combinación de filtros seleccionada.")
    st.stop()

# 3. PANORAMA EJECUTIVO (KPIs)
st.header("2. Panorama General e Indicadores Ejecutivos (KPIs)")

tot_casos = len(df_filtrado)
tot_dias = df_filtrado['dias_ausentismo'].sum()
prom_dias_caso = df_filtrado['dias_ausentismo'].mean()
tot_empleados = df_filtrado['id_empleado'].nunique()
costo_total_est = tot_dias * costo_dia_prom

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Casos Registrados", f"{tot_casos:,}")
k2.metric("Total Días Perdidos", f"{tot_dias:,} días")
k3.metric("Promedio Días / Caso", f"{prom_dias_caso:.1f} días")
k4.metric("Empleados Afectados", f"{tot_empleados:,}")
k5.metric("Costo Est. Ausentismo", f"${costo_total_est:,.0f}")

st.divider()

# 4. ESTRUCTURA EN PESTAÑAS CLAVE
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 1. Tendencia y Panorama General", 
    "🩺 2. Causa y Salud (Diagnósticos & EPS)", 
    "👥 3. Demográfico y Operativo (Puestos y Grupos)",
    "📋 4. Detalle y Exportación de Datos"
])

# --- PESTAÑA 1: PANORAMA Y TENDENCIA TEMPORAL ---
with tab1:
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        df_mes = df_filtrado.groupby('mes')['dias_ausentismo'].sum().reset_index()
        fig_mes = px.line(df_mes, x='mes', y='dias_ausentismo', markers=True, title="Evolución Mensual de Días de Ausentismo (Tendencia Temporal)", labels={'dias_ausentismo': 'Días Perdidos', 'mes': 'Mes'})
        fig_mes.update_traces(line_color='#1f77b4', line_width=3)
        st.plotly_chart(fig_mes, use_container_width=True)
    with col_t2:
        if 'tipo_prorroga' in df_filtrado.columns:
            df_pror = df_filtrado.groupby('tipo_prorroga')['dias_ausentismo'].sum().reset_index()
            fig_pror = px.pie(df_pror, values='dias_ausentismo', names='tipo_prorroga', title="Distribución: Eventos Nuevos vs. Prórrogas", hole=0.4)
            st.plotly_chart(fig_pror, use_container_width=True)

# --- PESTAÑA 2: CAUSA Y SALUD ---
with tab2:
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        df_tipo_g = df_filtrado.groupby('desc_tipo_ausentismo')['dias_ausentismo'].sum().reset_index().sort_values(by='dias_ausentismo', ascending=True)
        fig_tipo = px.bar(df_tipo_g, y='desc_tipo_ausentismo', x='dias_ausentismo', orientation='h', title="Días Perdidos por Tipo de Ausentismo", text_auto=True, color='dias_ausentismo')
        st.plotly_chart(fig_tipo, use_container_width=True)
    with col_d2:
        df_diag_g = df_filtrado.groupby('desc_diagnostico')['dias_ausentismo'].sum().reset_index().sort_values(by='dias_ausentismo', ascending=False).head(10)
        fig_diag = px.bar(df_diag_g, x='dias_ausentismo', y='desc_diagnostico', orientation='h', title="Top 10 Diagnósticos Médicos (CIE-10) con Mayor Impacto", text_auto=True)
        st.plotly_chart(fig_diag, use_container_width=True)
        
    st.divider()
    df_ent_g = df_filtrado[df_filtrado['nombre_entidad'] != "SIN ENTIDAD / NO APLICA"].groupby('nombre_entidad')['dias_ausentismo'].sum().reset_index().sort_values(by='dias_ausentismo', ascending=False).head(10)
    fig_ent = px.bar(df_ent_g, x='nombre_entidad', y='dias_ausentismo', title="Días Tramitados por Entidad de Salud (EPS / ARL)", text_auto=True, color_discrete_sequence=['#2ca02c'])
    st.plotly_chart(fig_ent, use_container_width=True)

# --- PESTAÑA 3: DEMOGRÁFICO Y OPERATIVO ---
with tab3:
    col_o1, col_o2 = st.columns(2)
    with col_o1:
        df_gen = df_filtrado.groupby('genero')['dias_ausentismo'].sum().reset_index()
        fig_gen = px.pie(df_gen, values='dias_ausentismo', names='genero', title="Severidad de Ausentismo (Días) por Género", hole=0.4)
        st.plotly_chart(fig_gen, use_container_width=True)
    with col_o2:
        df_cargo = df_filtrado.groupby('cargo')['dias_ausentismo'].sum().reset_index().sort_values(by='dias_ausentismo', ascending=False).head(10)
        fig_cargo = px.bar(df_cargo, x='dias_ausentismo', y='cargo', orientation='h', title="Top 10 Cargos con Mayor Ausentismo (Días)", text_auto=True)
        st.plotly_chart(fig_cargo, use_container_width=True)

    st.divider()
    col_o3, col_o4 = st.columns(2)
    with col_o3:
        df_grp = df_filtrado.groupby('nombre_grupo')['dias_ausentismo'].sum().reset_index().sort_values(by='dias_ausentismo', ascending=False).head(10)
        fig_grp = px.bar(df_grp, x='dias_ausentismo', y='nombre_grupo', orientation='h', title="Impacto por Grupo / Cliente (Top 10 Días)", text_auto=True, color_discrete_sequence=['#ff7f0e'])
        st.plotly_chart(fig_grp, use_container_width=True)
    with col_o4:
        top_emp_dias = df_filtrado.groupby(['id_empleado', 'nombre_completo', 'cargo'])['dias_ausentismo'].sum().reset_index().sort_values(by='dias_ausentismo', ascending=False).head(10)
        fig_top_d = px.bar(top_emp_dias, x='dias_ausentismo', y='nombre_completo', orientation='h', title="Top 10 Empleados con Mayor Recurrencia / Días", text_auto=True, color='dias_ausentismo')
        st.plotly_chart(fig_top_d, use_container_width=True)

# --- PESTAÑA 4: DETALLE Y EXPORTACIÓN ---
with tab4:
    st.subheader("📋 Registros Detallados y Exportación")
    
    df_export = df_filtrado.copy()
    if 'inicio_ausentismo' in df_export.columns:
        df_export['inicio_ausentismo'] = df_export['inicio_ausentismo'].dt.strftime('%d/%m/%Y')
    if 'final_ausentismo' in df_export.columns:
        df_export['final_ausentismo'] = df_export['final_ausentismo'].dt.strftime('%d/%m/%Y')
        
    columnas_ver = ['id_ausentismo', 'nombre_completo', 'cargo', 'agencia', 'nombre_grupo', 'desc_tipo_ausentismo', 'desc_diagnostico', 'nombre_entidad', 'dias_ausentismo', 'inicio_ausentismo', 'final_ausentismo', 'estado']
    cols_existentes = [c for c in columnas_ver if c in df_export.columns]
    
    st.dataframe(df_export[cols_existentes], use_container_width=True)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_export[cols_existentes].to_excel(writer, index=False, sheet_name='Ausentismo_Filtrado')
    
    st.download_button(
        label="📥 Descargar Reporte Filtrado a Excel",
        data=buffer.getvalue(),
        file_name="Reporte_Gerencial_Ausentismo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
