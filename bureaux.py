import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from streamlit_echarts import st_echarts
from utils import (charger_donnees_user, get_level, creer_domaine, obtenir_stats_completes,
                   supprimer_domaine, charger_quetes_user, valider_quete, preparer_donnees_echarts_bureau,
                   supprimer_quete, creer_quete, get_global_level, calculer_xp_noeud,calculer_fraicheur, obtenir_date_fraicheur_reelle)
from utils_ai import generer_suggestion_quete

# 1. CONFIGURATION
st.set_page_config(layout="wide", page_title="Bureaux de Domaine")

# 2. INITIALISATION
if "onglet_actuel" not in st.session_state:
    st.session_state.onglet_actuel = "Bureau"
if "domaine_actif" not in st.session_state:
    st.session_state.domaine_actif = None

# --- 3. RÉCUPÉRATION DES DONNÉES (BLOC SÉCURISÉ) ---
user = st.session_state.username
df_user = charger_donnees_user(user)
domaine = st.session_state.get('domaine_actif')

if domaine:
    df_selection = df_user[df_user['ID'] == domaine]
    
    if not df_selection.empty:
        row_domaine = df_selection.iloc[0]
        
        stats = obtenir_stats_completes(df_user, domaine)
        lvl_domaine = stats['lvl']
        xp_actuelle = stats['xp']
        pct_lvl = stats['pct']
        date_la_plus_recente = obtenir_date_fraicheur_reelle(df_user, domaine)
        fraicheur = calculer_fraicheur(date_la_plus_recente)

# --- NAVIGATION ---

cols_nav = st.columns([1, 1, 1])
if cols_nav[0].button("🏢 Bureau", use_container_width=True):
    st.session_state.onglet_actuel = "Bureau"
    st.rerun()
if cols_nav[1].button("🗄️ Tiroir de Domaine", use_container_width=True):
    st.session_state.onglet_actuel = "Tiroir"
    st.rerun()
if cols_nav[2].button("🛠️ Création / Gestion", use_container_width=True):
    st.session_state.onglet_actuel = "Gestion"
    st.rerun()

st.divider()

# --- LOGIQUE D'AFFICHAGE SELON L'ONGLET ---

# --- ONGLET 1 : BUREAU ---
if st.session_state.onglet_actuel == "Bureau":
    if not domaine:
        st.warning("⚠️ Veuillez sélectionner un domaine dans le Tiroir ou l'Arbre.")
    else:
        nom_titre = row_domaine['Label'] if row_domaine is not None else "Sélectionnez un domaine"
        st.title(f"📂 Bureau : {nom_titre}")

        # Préparation Radar Chart
        if "zoom_bureau" not in st.session_state:
            st.session_state.zoom_bureau = False
        
        mode_zoom = st.session_state.zoom_bureau
        sous_comp = df_user[df_user['Parent'] == domaine]
        fig = None

        if not sous_comp.empty and len(sous_comp) >= 3:
            labels = sous_comp['Label'].tolist()
            levels = []
            for _, row in sous_comp.iterrows():
                total_xp_branche = calculer_xp_noeud(df_user, row['ID'])
                lvl = float(get_level(total_xp_branche))
                levels.append(lvl)
            max_actuel = max(levels) if levels else 0
            range_r = [0, max(10, (max_actuel // 5 + 1) * 5)] if mode_zoom else [0, 100]
            
            labels_closed = labels + [labels[0]]
            levels_closed = levels + [levels[0]]
            
            fig = go.Figure()
            fig.add_trace(go.Scatterpolar(
                r=levels_closed, theta=labels_closed, fill='toself',
                mode='lines+markers', fillcolor='rgba(255, 190, 190, 0.2)',
                line=dict(color="#991515", width=3), marker=dict(size=6)
            ))
            fig.update_layout(
                polar=dict(gridshape='linear', radialaxis=dict(visible=True, range=range_r, gridcolor="#444"),
                angularaxis=dict(visible=True, gridcolor="#444", tickfont=dict(color="white")),
                bgcolor="rgba(0,0,0,0)"), showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)", template="plotly_dark", margin=dict(l=40, r=40, t=30, b=30)
            )

        col1, col2 = st.columns([0.4, 0.6])
        
        with col1:
            with st.container(height=530):
                st.toggle("🔍 Zoom Focus", key="zoom_bureau")
                if fig: st.plotly_chart(fig, width='stretch')
                else: st.info("Besoin d'au moins 3 sous-compétences.")

        with col2:
            with st.container(height=530):
                # 1. RÉCUPÉRATION ET FILTRAGE
                df_q = charger_quetes_user(user)
                famille_ids = df_user[df_user['Parent'] == domaine]['ID'].tolist() + [domaine]
                
                # --- SECTION : QUÊTE PRINCIPALE ---
                st.subheader("🌟 Quête Principale")
                mask_p = (df_q['Statut'] == "En cours") & \
                        (df_q['ID_Competence'].isin(famille_ids)) & \
                        (df_q['Type'] == "Principale")
                q_principale = df_q[mask_p]

                if q_principale.empty:
                    st.info("Aucun grand défi en cours. Forges-en un !")
                else:
                    for _, q in q_principale.iterrows():
                        with st.info('body'):
                            c1, c2 = st.columns([0.8, 0.2])
                            c1.markdown(f"### 👑 {q['Titre']}")
                            c1.write(f"Récompense massive : **{q['XP_Recompense']} XP**")
                            if c2.button("✅", key=f"val_{q['ID_Quete']}"):
                                valider_quete(user, q['ID_Quete'])
                                st.rerun()

                st.write("---")
                
                # --- SECTION : QUÊTES SECONDAIRES ---
                st.subheader("🎯 Objectifs Secondaires")
                mask_s = (df_q['Statut'] == "En cours") & \
                        (df_q['ID_Competence'].isin(famille_ids)) & \
                        (df_q['Type'] == "Secondaire")
                q_secondaires = df_q[mask_s]

                if q_secondaires.empty:
                    st.write("🍃 Repos de l'aventurier...")
                else:
                    for i, (_, q) in enumerate(q_secondaires.iterrows()):
                        with st.container(border=True):
                            c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
                            c1.write(f"**{q['Titre']}**")
                            c1.caption(f"🏆 {q['XP_Recompense']} XP")
                            if c2.button("✅", key=f"vs_{q['ID_Quete']}_{i}"):
                                valider_quete(user, q['ID_Quete'])
                                st.rerun()
                            if c3.button("🗑️", key=f"ds_{q['ID_Quete']}_{i}"):
                                supprimer_quete(user, q['ID_Quete'])
                                st.rerun()
        col3,col4 = st.columns([0.3,0.7],border=True)
        with col3:
            with st.container():
                    icon = "🍏" if fraicheur > 70 else "🟠" if fraicheur > 30 else "💀"
                    st.write(f"{icon} **Fraîcheur de la compétence : {fraicheur}%**")
                    st.progress(fraicheur / 100)

        with col4:
            with st.container(height='stretch'):
                st.subheader("📉 Flux de Progression")

                choix_periode = st.radio("Période", ["Semaine", "Mois"], horizontal=True)
                dates, series, labels = preparer_donnees_echarts_bureau(user, domaine, choix_periode)

                if series:
                    options = {
                        "tooltip": {"trigger": "axis", "backgroundColor": "rgba(0,0,0,0.7)", "textStyle": {"color": "#fff"}},
                        "legend": {"data": labels, "textStyle": {"color": "#ccc"}, "top": "5%"},
                        "xAxis": {
                            "type": "category",
                            "data": dates,
                            "axisLine": {"lineStyle": {"color": "#666"}}
                        },
                        "yAxis": {
                            "type": "value",
                            "splitLine": {"lineStyle": {"color": "#333"}},
                            "axisLine": {"show": False}
                        },
                        "series": series,
                        "grid": {"left": "3%", "right": "4%", "bottom": "3%", "containLabel": True}
                    }
                    
                    st_echarts(options=options, width='100%',height="200px")
                else:
                    st.info("Aucune donnée d'XP pour le moment dans ces sous-domaines.")

        with st.container(height='stretch'):
            st.subheader("🛠️ Forge des Quêtes")
            
            # --- BLOC IA ---
            with st.expander("✨ Invoquer l'Oracle", expanded=False):
                st.select_slider(
                    "Intensité du défi",
                    options=["Petite", "Soutenue", "Épique"],
                    value="Soutenue",
                    key="intensite_choisie" 
                )
                
                seed = st.text_input("Une idée ? (Ex: Sport, Code...)", key="seed_joueur")

                if st.button("🔮 Générer la quête"):
                    with st.spinner("L'Oracle forge ton destin..."):
                        intensite_actuelle = st.session_state.intensite_choisie
                        inspiration = st.session_state.seed_joueur
                        
                        # On envoie l'intensité à la fonction
                        prop = generer_suggestion_quete(df_user, domaine, intensite_actuelle, inspiration)
                        
                        if "error" not in prop:
                            # Calcul de l'XP avec le multiplicateur de difficulté du MONDE
                            coef = {"Facile": 2.5, "Normal": 1.0, "Difficile": 0.7}.get(st.session_state.difficulte, 1.0)
                            
                            st.session_state.temp_titre = prop['titre']
                            st.session_state.temp_xp = int(prop['xp_base'] * coef)
                            st.session_state.temp_expl = prop['explication']
                            st.rerun()

            with st.expander("🔨 Forger une Quête", expanded=False):
                with st.form("form_nouvelle_quete", clear_on_submit=True):
                    t_val = st.session_state.get('temp_titre', "")
                    xp_val = st.session_state.get('temp_xp', 50)
                    type_val = st.session_state.get('temp_type', "Secondaire")
                    
                    titre = st.text_input("Nom de la quête", value=t_val)
                    
                    sous_domaines_dispo = df_user[df_user['Parent'] == domaine]
                    options_sd = dict(zip(sous_domaines_dispo['Label'], sous_domaines_dispo['ID']))
                    
                    # Si pas de sous-domaine, on cible le domaine lui-même
                    if not options_sd:
                        options_sd = {domaine: domaine}

                    target_id = st.selectbox("Cible", options=options_sd.keys())
                    q_type = st.radio("Type", ["Secondaire", "Principale"], 
                                    index=0 if type_val == "Secondaire" else 1, 
                                    horizontal=True)
                    
                    q_xp = st.number_input("Récompense XP", value=int(xp_val))
                    
                    if st.form_submit_button("🔨 Forger la quête", use_container_width=True):
                        if titre:
                            succes, msg = creer_quete(user, options_sd[target_id], titre, q_xp, q_type)
                            if succes:
                                # On vide les variables temporaires de l'IA après succès
                                for key in ['temp_titre', 'temp_xp', 'temp_type']:
                                    if key in st.session_state: del st.session_state[key]
                                st.toast(msg)
                                st.rerun()
                            else:
                                st.error(msg)

# --- ONGLET 2 : TIROIR ---
elif st.session_state.onglet_actuel == "Tiroir":
    st.subheader("🗄️ Tiroir des Domaines")
    
    # On ne garde que les domaines qui ont 'GLO' comme parent (Les racines)
    domaines_racines = df_user[df_user['Parent'] == 'GLO']
    
    if domaines_racines.empty:
        st.info("Plante ta première graine dans l'Arbre des Compétences.")
    else:
        cols = st.columns(2)
        for i, (_, row) in enumerate(domaines_racines.iterrows()):
            with cols[i % 2]:
                with st.container(border=True):
                    st.markdown(f"### {row['Label']}")
                    # Optionnel : Afficher le niveau global du domaine
                    lvl = get_level(calculer_xp_noeud(df_user, row['ID']))
                    st.caption(f"Maîtrise Totale : Niveau {lvl}")
                    
                    if st.button(f"Ouvrir le bureau", key=f"open_{row['ID']}", use_container_width=True):
                        st.session_state.domaine_actif = row['ID']
                        st.session_state.onglet_actuel = "Bureau"
                        st.rerun()

# --- ONGLET 3 : GESTION ---
elif st.session_state.onglet_actuel == "Gestion":

    st.subheader("⚒️ Forge")

    with st.expander("Créer un Domaine", expanded=False):
        st.subheader("⚒️ Forge de nouveaux Domaines")
        df_parent = df_user[df_user['Parent'] != 'META'].copy()
        options_domaines = dict(zip(df_parent['Label'], df_parent['ID']))
        with st.form("form_nouveau_domaine"):
            nouveau_nom = st.text_input("Nom du futur domaine")
            label_parent = st.selectbox("Domaine Parent", options=options_domaines.keys())
            if st.form_submit_button("🔨 Forger le Domaine"):
                if nouveau_nom:
                    creer_domaine(user, options_domaines[label_parent], nouveau_nom)
                    st.success("Domaine créé !")
                    st.rerun()
    st.divider()
    st.subheader("🗑️ Zone de Danger")

    with st.expander("Supprimer un Domaine", expanded=False):
        # On propose de supprimer n'importe quel domaine sauf Global
        options_suppr = {row['Label']: row['ID'] for _, row in df_user.iterrows() if row['ID'] != "GLO"}
        
        domaine_a_suppr_label = st.selectbox("Choisir le domaine à effacer", options=list(options_suppr.keys()), key="select_suppr")
        id_a_suppr = options_suppr[domaine_a_suppr_label]
        
        st.warning(f"Attention, supprimer '{domaine_a_suppr_label}' est irréversible.")
        
        if st.button(f"Confirmer la suppression de {id_a_suppr}", type="primary"):
            success, message = supprimer_domaine(user, id_a_suppr)
            if success:
                st.success(message)
                # Si on vient de supprimer le domaine sur lequel on était, on reset
                if st.session_state.domaine_actif == id_a_suppr:
                    st.session_state.domaine_actif = "GLO"
                st.rerun()
            else:
                st.error(message)