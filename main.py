import streamlit as st
import pandas as pd
import os
from utils import get_global_level, charger_donnees_user,appliquer_atrophie

# --- 1. CONFIGURATION DE L'ÉTAT ---
if "username" not in st.session_state:
    st.session_state.username = None

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# --- 2. FONCTIONS DE GESTION DES UTILISATEURS ---
def gerer_inscription(new_u, new_p):
    if not new_u or not new_p:
        st.error("Veuillez remplir tous les champs.")
        return
    
    file = "users.csv"
    # Charger ou créer le fichier des utilisateurs
    if os.path.exists(file):
        df = pd.read_csv(file)
    else:
        df = pd.DataFrame(columns=['user', 'pw'])

    # Vérifier si le pseudo existe déjà
    if new_u in df['user'].values:
        st.error("Ce pseudo est déjà utilisé par un autre héros.")
    else:
        # Ajouter le nouvel utilisateur
        new_row = pd.DataFrame([{'user': new_u, 'pw': new_p}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(file, index=False)
        
        # CRUCIAL : Créer le fichier de données du joueur immédiatement
        # pour éviter les erreurs au premier login
        charger_donnees_user(new_u) 
        
        st.success("Compte créé avec succès ! Tu peux maintenant te connecter.")

# --- 3. DÉFINITION DE LA PAGE DE LOGIN ---
def login_page():
    st.title("🏹 Le Jeu de la Vie : L'éveil")
    
    tab_login, tab_sign_up = st.tabs(["🔒 Connexion", "📝 Créer un compte"])

    with tab_login:
        with st.container(border=True):
            u = st.text_input("Pseudo", key="login_user")
            p = st.text_input("Mot de passe", type="password", key="login_pw")
            if st.button("Entrer dans l'aventure"):
                if os.path.exists("users.csv"):
                    df = pd.read_csv("users.csv")
                    user_match = df[(df['user'] == u) & (df['pw'].astype(str) == p)]
                    if not user_match.empty:
                        st.session_state.logged_in = True
                        st.session_state.username = u 
                        st.rerun()
                st.error("Identifiants incorrects ou compte inexistant.")

    with tab_sign_up:
        with st.container(border=True):
            new_u = st.text_input("Choisir un pseudo", key="signup_user")
            new_p = st.text_input("Choisir un mot de passe", type="password", key="signup_pw")
            if st.button("Forger mon destin"):
                gerer_inscription(new_u, new_p)

# --- 4. NAVIGATION ET LOGIQUE GLOBALE ---
login_screen = st.Page(login_page, title="Connexion", icon="🔒")
page_1 = st.Page("accueil.py", title="Accueil", icon="🏠")
page_2 = st.Page("arbre.py", title="Arbre des Compétences", icon="🌳")
page_3 = st.Page("bureaux.py", title="Bureaux de Domaine", icon="📂")
page_4 = st.Page("journal.py", title="Journal de Quêtes", icon="🗒️")
page_5 = st.Page("oracle.py", title="Antre de l'Oracle", icon="🔮")
page_6 = st.Page("settings.py", title="Paramètres", icon="⚙️")

if not st.session_state.logged_in:
    pg = st.navigation([login_screen])
else:
    # ON NE CALCULE LE NIVEAU QUE SI ON EST CONNECTÉ (Bye bye data_None.csv !)
    if "atrophie_calculee" not in st.session_state:
        # On lance le calcul de perte d'XP une seule fois par session
        perte_detectee = appliquer_atrophie(st.session_state.username)
        if perte_detectee:
            st.toast("⚠️ Tes compétences s'atrophient par manque de pratique...", icon="📉")
        st.session_state.atrophie_calculee = True
    lvl_global = get_global_level(st.session_state.username)
    
    pg = st.navigation([page_1, page_2, page_3, page_4, page_5, page_6])
    
    if "difficulte" not in st.session_state:
        st.session_state.difficulte = "Normal"

    with st.sidebar:
        st.sidebar.metric("🌟 Niveau Global", f"LVL {lvl_global}")
        st.sidebar.progress(lvl_global / 100)

pg.run()