import streamlit as st
import pandas as pd
from utils import charger_donnees_user, get_global_level, calculer_fraicheur,obtenir_date_fraicheur_reelle # Ajoute calculer_fraicheur
from utils_ai import demander_conseil_oracle, preparer_contexte_ia

st.set_page_config(layout="wide",page_title="L'antre de l'Oracle")

user = st.session_state.username
df_user = charger_donnees_user(user)
lvl_global = get_global_level(user)
contexte_ia = preparer_contexte_ia(df_user, user)

# --- STYLE CSS POUR L'IMMERSION ---
st.markdown("""
    <style>
    .oracle-card {
        background: rgba(15, 174, 185, 0.05);
        border-left: 5px solid #0faeb9;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .vision-title {
        color: #0faeb9;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    </style>
""", unsafe_allow_html=True)

# --- ENTÊTE ÉPIQUE ---
st.title("🔮 L'Antre de l'Oracle")
st.caption("Le temps s'arrête ici. Écoute les murmures de ta propre progression.")

col_stats, col_chat = st.columns([0.4, 0.6], gap="large")

with col_stats:
    st.markdown("<p class='vision-title'>✨ Miroir du Destin</p>", unsafe_allow_html=True)
    
    with st.container(border=True):
        # --- 1. FILTRAGE INTELLIGENT ---
        # On exclut le META et le GLO technique
        df_game = df_user[(df_user['Parent'] != 'META') & (df_user['ID'] != 'GLO')].copy()
        
        # On identifie les "Feuilles" (domaines qui ne sont les parents de personne)
        # C'est là que l'XP est réellement injectée (ex: Boxe, Foot)
        ids_qui_sont_parents = df_game['Parent'].unique()
        df_feuilles = df_game[~df_game['ID'].isin(ids_qui_sont_parents)]

        # --- 2. FORCES ET FAIBLESSES (Basées sur les feuilles) ---
        if not df_feuilles.empty:
            domaine_faible = df_feuilles.loc[df_feuilles['XP'].idxmin()]['Label']
            domaine_fort = df_feuilles.loc[df_feuilles['XP'].idxmax()]['Label']
            
            st.write(f"🛡️ **Ta plus grande force :** {domaine_fort}")
            st.write(f"⚠️ **Ton point de vulnérabilité :** {domaine_faible}")
        else:
            st.write("🌌 Ton destin est encore une page blanche.")
        
        st.divider()
        
        # --- 3. MURMURES DE L'OUBLI (Basés sur les parents pour la clarté) ---
        st.write("🌀 **Murmures de l'Oubli**")
        alertes = 0

        df_racines = df_game[(df_game['Parent'] == 'GLO') | (df_game['Parent'].isna()) | (df_game['Parent'] == '')]

        for _, row in df_racines.iterrows():
            date_reelle = obtenir_date_fraicheur_reelle(df_user, row['ID'])
            f = calculer_fraicheur(date_reelle)
            
            if f < 50:
                st.caption(f"{row['Label']} s'efface... ({f}%)")
                st.progress(f / 100)
                alertes += 1

        # --- 4. BILAN GLOBAL (HORS DE LA BOUCLE !) ---
        if alertes == 0:
            st.write("✅ Tes connaissances sont vives et alertes.")
            
            # Conseil passif basé sur l'Aura
            if lvl_global < 20:
                st.info("L'Oracle voit que ton Aura globale est encore fragile. Diversifie tes quêtes.")
            else:
                st.success("Ton aura grandit. La maîtrise est à portée de main.")

    # Boutons de "Sacrifice" (Quick Prompts)
    st.markdown("### 🏺 Offrandes de pensée")
    if st.button("⚖️ Analyse mon équilibre de vie", use_container_width=True):
        st.session_state.oracle_input = "Analyse mes domaines actuels et dis-moi si ma vie est équilibrée ou si je néglige un aspect crucial."
    
    if st.button("🚀 Comment atteindre le niveau suivant ?", use_container_width=True):
        st.session_state.oracle_input = f"Je suis niveau {lvl_global}. Donne-moi une stratégie concrète pour passer au niveau supérieur rapidement."

# --- COLONNE DROITE : LE DIALOGUE ---
with col_chat:
    st.markdown("<p class='vision-title'>💬 Dialogue Sacré</p>", unsafe_allow_html=True)
    
    # Zone de discussion
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Affichage du chat
    chat_container = st.container(height=450)
    for msg in st.session_state.chat_history:
        with chat_container.chat_message(msg["role"]):
            st.write(msg["content"])

    # Input utilisateur
    user_query = st.chat_input("Pose ta question à l'Oracle...")
    
    final_query = user_query if user_query else st.session_state.get('oracle_input', None)

    if final_query:
        st.session_state.chat_history.append({"role": "user", "content": final_query})
        with chat_container.chat_message("user"):
            st.write(final_query)

        with st.spinner("L'Oracle consulte les archives de ton âme..."):
            reponse = demander_conseil_oracle(contexte_ia, final_query)
            
            full_response = reponse['reponse']
            if reponse.get('suggestion_domaine'):
                full_response += f"\n\n💎 **Une voie s'éclaire :** Tu devrais explorer le domaine '{reponse['suggestion_domaine']}'."

            st.session_state.chat_history.append({"role": "assistant", "content": full_response})
            with chat_container.chat_message("assistant"):
                st.write(full_response)
        
        if 'oracle_input' in st.session_state:
            del st.session_state.oracle_input
        st.rerun()

st.divider()
st.caption("Rappelle-toi Aventurier : l'Oracle guide, mais c'est ton bras qui forge.")