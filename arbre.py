import streamlit as st
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config
from utils import charger_donnees_user,sauvegarder_donnees_user,securite_page,est_domaine_principal
#📂
user = st.session_state.username
df_total = charger_donnees_user(user)
securite_page()
df_arbre = df_total[df_total['Parent'] != 'META'].copy()

st.set_page_config(layout="wide", page_title="Arbre de Compétences")

# --- CONFIGURATION DES COULEURS (Bonus) ---
# On crée un dégradé du plus foncé (racine) au plus clair (feuilles)
PALETTE_COULEURS = {
    0: "#1B4F72", # Racine (Bleu très foncé)
    1: "#2874A6", # Niveau 1
    2: "#3498DB", # Niveau 2
    3: "#85C1E9", # Niveau 3
    4: "#AED6F1"  # Niveau 4+
}

def calculer_profondeur(df_arbre, node_id):
    """Compte le nombre de pas pour remonter à la racine."""
    profondeur = 0
    current_id = node_id
    
    # On remonte tant qu'on trouve un parent valide
    while True:
        # On cherche la ligne de l'ID actuel
        ligne = df_arbre[df_arbre['ID'] == current_id]
        if ligne.empty:
            break
            
        parent = ligne.iloc[0]['Parent']
        
        # Si le parent est vide ou None, on est à la racine
        if pd.isna(parent) or parent == "" or parent == "None":
            break
        else:
            current_id = parent
            profondeur += 1
            
    return profondeur

def generer_arbre_dynamique(df_arbre):
    nodes = []
    edges = []
    
    # --- NETTOYAGE PRÉVENTIF ---
    # On remplace les NaN par des chaînes vides pour éviter l'erreur JSON
    df_arbre = df_arbre.fillna("")

    for _, row in df_arbre.iterrows():
        # 1. Calcul de la profondeur pour ce nœud
        prof = calculer_profondeur(df_arbre, row['ID'])
        
        # 2. Calcul de la taille (décroissante)
        # On part de 40px et on réduit de 20% à chaque niveau
        taille = 40 * (0.8 ** prof)
        
        # 3. Choix de la couleur selon la profondeur
        couleur = PALETTE_COULEURS.get(prof, PALETTE_COULEURS[4])

        # 4. Création du Noeud
        nodes.append(Node(
            id=row['ID'], 
            label=f"{row['Label']}", 
            size=taille, 
            color=couleur,
            font={
            "color": "#ffffff", # Blanc pur
            "size": 14,
            "face": "Arial"
        }
        ))

        # 5. Création du Lien (uniquement si un parent existe)
        if row['Parent'] != "":
            edges.append(Edge(
                source=row['Parent'], 
                target=row['ID'], 
                color="#D5D8DC" # Gris clair pour les liens
            ))
            
    return nodes, edges

# --- INTERFACE STREAMLIT ---

# 1. Utiliser le mode large
st.set_page_config(layout="wide")

# 2. CSS pour réduire le padding (espace sur les bords)
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 0rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌳 Arbre de Compétences Hiérarchique")

if df_arbre is not None:
    nodes,edges = generer_arbre_dynamique(df_arbre)

# Configuration visuelle
config = Config(
    width='stretch', 
    height=600,
    node={
        'labelProperty': 'label',
        'font': {
            'color': '#ffffff', # Blanc pur pour la lisibilité
            'size': 14,
            'face': 'sans-serif'
        }
    },
    link={'color': '#727272'},
    hierarchical=True, # L'arbre se range tout seul
    direction='UD',    # De haut en bas (Up-Down)
    sortMethod='directed',
    font={'color':'red'}, # Cor global para todos os rótulos
    physics=False      # On fige la position pour plus de clarté
)

# Affichage
node_id_clique = agraph(nodes=nodes, edges=edges, config=config)

if node_id_clique:
    # 1. Ta logique de vérification (est-ce un domaine principal ?)
    # On imagine une fonction dans utils.py qui fait ce check
    if est_domaine_principal(df_arbre, node_id_clique):
        
        # 2. ON DÉPOSE LA VARIABLE DANS LE SESSION_STATE
        st.session_state.domaine_actif = node_id_clique
        
        # 3. ON FORCE LA REDIRECTION VERS LA PAGE BUREAUX
        # Utilise exactement le nom du fichier défini dans ton main.py
        st.switch_page("bureaux.py")
    else:
        st.sidebar.info("Ceci est une compétence finale.")