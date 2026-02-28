import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF

# 1. CONFIGURACIÓN Y ESTADO DE LA APP
st.set_page_config(page_title="BasketStats Pro 2026", layout="wide")

if 'score_home' not in st.session_state:
    st.session_state.update({
        'score_home': 0, 'score_away': 0,
        'shot_data': pd.DataFrame(columns=['x', 'y', 'resultado']),
        'players_stats': pd.DataFrame({
            "Jugador": ["Jugador 1", "Jugador 2", "Jugador 3", "Jugador 4", "Jugador 5"],
            "Puntos": [0]*5, "Rebotes": [0]*5, "Asistencias": [0]*5, "Faltas": [0]*5
        })
    })

# --- BARRA LATERAL: MARCADOR GLOBAL ---
with st.sidebar:
    st.header("🏀 Marcador")
    col_s1, col_s2 = st.columns(2)
    col_s1.metric("LOCAL", st.session_state.score_home)
    col_s2.metric("VISITANTE", st.session_state.score_away)
    
    if st.button("🔄 Resetear Partido"):
        st.session_state.clear()
        st.rerun()

# --- SECCIÓN 1: REGISTRO DE ACCIONES ---
st.title("📊 Gestión de Partido en Vivo")
c1, c2 = st.columns([1, 2])

with c1:
    st.subheader("Registrar Acción")
    jugador = st.selectbox("Selecciona Jugador", st.session_state.players_stats["Jugador"])
    accion = st.radio("Acción", ["Canasta +2", "Triple +3", "Tiro Libre +1", "Rebote", "Asistencia", "Falta"], horizontal=True)
    
    # Coordenadas para el Mapa de Calor
    st.write("Ubicación del tiro:")
    px_tiro = st.slider("Lateral (X)", 0, 100, 50)
    py_tiro = st.slider("Distancia (Y)", 0, 100, 20)
    
    if st.button("Confirmar ✅", use_container_width=True):
        idx = st.session_state.players_stats.index[st.session_state.players_stats["Jugador"] == jugador][0]
        puntos_a_sumar = 0
        
        if "Canasta" in accion: puntos_a_sumar = 2
        elif "Triple" in accion: puntos_a_sumar = 3
        elif "Libre" in accion: puntos_a_sumar = 1
        elif "Rebote" in accion: st.session_state.players_stats.at[idx, "Rebotes"] += 1
        elif "Asistencia" in accion: st.session_state.players_stats.at[idx, "Asistencias"] += 1
        elif "Falta" in accion: st.session_state.players_stats.at[idx, "Faltas"] += 1

        if puntos_a_sumar > 0:
            st.session_state.players_stats.at[idx, "Puntos"] += puntos_a_sumar
            st.session_state.score_home += puntos_a_sumar
            # Guardar para el mapa de calor
            nuevo_tiro = pd.DataFrame({'x': [px_tiro], 'y': [py_tiro], 'resultado': ['Anotado']})
            st.session_state.shot_data = pd.concat([st.session_state.shot_data, nuevo_tiro], ignore_index=True)
        st.rerun()

# --- SECCIÓN 2: VISUALIZACIÓN ---
with c2:
    tab1, tab2, tab3 = st.tabs(["📊 Estadísticas", "📍 Mapa de Calor", "📈 Gráficos"])
    
    with tab1:
        st.dataframe(st.session_state.players_stats, use_container_width=True, hide_index=True)
        tiros_totales = len(st.session_state.shot_data)
        if tiros_totales > 0:
            efectividad = (len(st.session_state.shot_data[st.session_state.shot_data['resultado']=='Anotado']) / tiros_totales) * 100
            st.metric("Efectividad de Campo (FG%)", f"{efectividad:.1f}%")

    with tab2:
        fig_cancha = go.Figure()
        fig_cancha.add_trace(go.Scatter(
            x=st.session_state.shot_data['x'], y=st.session_state.shot_data['y'],
            mode='markers', marker=dict(color='green', size=15, symbol='circle'), name="Anotado"
        ))
        fig_cancha.update_layout(width=500, height=400, xaxis=dict(range=[0, 100]), yaxis=dict(range=[0, 100]), 
                                 paper_bgcolor="lightgrey", title="Distribución de Tiros")
        st.plotly_chart(fig_cancha)

    with tab3:
        fig_bar = px.bar(st.session_state.players_stats, x="Jugador", y="Puntos", color="Puntos", text="Puntos")
        st.plotly_chart(fig_bar, use_container_width=True)

# --- SECCIÓN 3: EXPORTAR ---
st.divider()
def export_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Reporte Final de Partido", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    for _, r in df.iterrows():
        pdf.cell(0, 10, f"{r['Jugador']}: {r['Puntos']} Pts | {r['Rebotes']} Reb | {r['Faltas']} Faltas", ln=True)
    return pdf.output
st.download_button("📩 Descargar Acta en PDF", data=export_pdf(st.session_state.players_stats), file_name="partido.pdf")
