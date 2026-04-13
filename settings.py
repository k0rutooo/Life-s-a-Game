import streamlit as st
from utils import (obtenir_difficulte_jeu,sauvegarder_difficulte_jeu,)

user = st.session_state.username
difficulty = obtenir_difficulte_jeu(user)

#ici mettre de quoi importer et exporter les données utilisateurs
#mettre des commentaires partout dans le programme pour qu'il soit facilement compréhensible et modifiable par tout le monde

# --- Dans bureaux.py ou accueil.py (Onglet Gestion/Paramètres) ---
st.subheader("⚙️ Paramètres du Monde")

with st.container(border=True):
    diff_actuelle = obtenir_difficulte_jeu(user) # On lit depuis le CSV via utils.py
    
    nouvelle_diff = st.select_slider(
        "Difficulté Globale",
        options=["Facile", "Normal", "Difficile"],
        value=diff_actuelle
    )

    # Affichage des règles du monde (Bonus/Malus)
    cols = st.columns(3)
    with cols[0]:
        st.markdown("🟢 **Facile**")
        st.caption("Progression x2.5\nIdéal pour débuter.")
    with cols[1]:
        st.markdown("⚪ **Normal**")
        st.caption("Progression x1.0\nL'équilibre parfait.")
    with cols[2]:
        st.markdown("🔴 **Difficile**")
        st.caption("Progression x0.7\nLe vrai défi.")

    if nouvelle_diff != diff_actuelle:
        sauvegarder_difficulte_jeu(user, nouvelle_diff)
        st.session_state.difficulte = nouvelle_diff # Mise à jour live
        st.success(f"Le monde est désormais en mode {nouvelle_diff} !")

if st.button("Déconnexion"):
    st.session_state.logged_in = False
    st.rerun()