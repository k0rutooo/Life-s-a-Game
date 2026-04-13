import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts
from PIL import Image
from utils import charger_donnees_user, get_global_level, charger_quetes_user,preparer_donnees_graphique,obtenir_titre_rang
from utils_asset import get_rang_image

# --- 1. CONFIGURATION (TOUJOURS EN PREMIER) ---
st.set_page_config(layout="wide", page_title="Hall des Héros")

# --- 2. RÉCUPÉRATION DES DONNÉES ---
user = st.session_state.username
df_user = charger_donnees_user(user)
lvl_global = get_global_level(user)
df_q = charger_quetes_user(user)
titre = obtenir_titre_rang(lvl_global)

# --- 3. LAYOUT & STYLE ---
st.markdown("""
<style>
    .block-container { padding-top: 3rem; }
</style>
""", unsafe_allow_html=True)

# --- LIGNE 1 : PROFIL & NIVEAU ---
col1, col2 = st.columns([0.7, 0.3])

with col1:
    with st.container(border=True,height='stretch'):
        st.title(f"🛡️ Profil de {user}")
        st.divider()
        
        # On récupère les titres des quêtes principales actives
        quetes_p = df_q[(df_q['Statut'] == "En cours") & (df_q['Type'] == "Principale")]
        
        if not quetes_p.empty:
            option_q = st.selectbox("Focus Actuel :", quetes_p['Titre'].tolist())
            st.info(f"Objectif : {option_q}")
        else:
            st.warning("Aucune Quête Principale assignée. Forge ton destin dans un Bureau !")

with col2:
    with st.container(border= True,height='stretch'):
        try:
            st.markdown(
            """
            <style>
            button[title="View fullscreen"] {
                display: none;
            }
            [data-testid="stImage"] {
                pointer-events: none;
            }
            </style>
            """,
            unsafe_allow_html=True
            )
            st.image(get_rang_image(lvl_global))

        except FileNotFoundError:
            st.error("Le fichier png est introuvable. Veuillez le charger.")
# --- LIGNE 2 : STATS & GRAPHIQUE ---

with st.container(height='stretch',border=True):
    # 1. Sélecteur de période
    periode = st.radio("Vue temporelle", ["Semaine", "Mois", "Année"], horizontal=True, label_visibility="collapsed")
    
    # 2. Récupération des données
    data_graph = preparer_donnees_graphique(user, periode)
    
    if data_graph.empty:
        st.info("Forge et termine des quêtes pour voir ton évolution !")
    else:
        # Préparation des listes pour ECharts
        dates = data_graph['Date'].dt.strftime('%d/%m').tolist()
        valeurs = data_graph['XP'].tolist()

        # 3. Configuration de ECharts
        options = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {
                "type": "category",
                "data": dates,
                "axisLabel": {"color": "#888"}
            },
            "yAxis": {
                "type": "value",
                "splitLine": {
                    "lineStyle": {
                        "color": "#888", # Un peu plus clair que le fond pour être subtil
                        "type": "dashed" # Optionnel : quadrillage en pointillés
                    }
                },
                "axisLabel": {"color": "#BCBCBC"}
            },
            "series": [
                {
                    "data": valeurs,
                    "type": "line",
                    "smooth": True,
                    "symbol": "none",
                    "lineStyle": {"color": "#CB2424", "width": 3},
                    "areaStyle": {
                        "color": "rgba(255, 120, 120, 0.2)" # Petit effet de remplissage sous la courbe
                    },
                }
            ],
            "backgroundColor": "transparent",
            "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True}
        }
        
        st_echarts(options=options, height="280px")