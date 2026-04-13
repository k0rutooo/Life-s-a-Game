import openai
import json
import requests
import streamlit as st
from utils import calculer_fraicheur,get_level,get_global_level

def recuperer_top_modeles_gratuits(limite=5):
    """
    Interroge l'API d'OpenRouter pour trouver les modèles dont l'ID finit par ':free'.
    """
    url = "https://openrouter.ai/api/v1/models"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            all_models = response.json().get('data', [])
            
            # 1. On filtre uniquement ceux qui finissent par ':free'
            # (Optionnel : on pourrait aussi vérifier si pricing['prompt'] == "0")
            free_models = [m['id'] for m in all_models if m['id'].endswith(':free')]
            
            # 2. On retourne les X premiers
            return free_models[:limite]
        else:
            return []
    except Exception as e:
        print(f"Erreur lors de la récupération des modèles : {e}")
        return []

# On récupère les modèles frais au lancement
modeles_dynamiques = recuperer_top_modeles_gratuits(5)

# On construit notre liste finale
# 'openrouter/free' est le joker qui marche presque tout le temps
MODELES_PRIORITAIRES = ["openrouter/free"] + modeles_dynamiques

# Si la liste est vide (problème réseau), on met des valeurs de secours par défaut
if len(MODELES_PRIORITAIRES) <= 1:
    MODELES_PRIORITAIRES += [
        "google/gemini-2.0-flash-exp:free",      # Très intelligent, bon en français
        "meta-llama/llama-3.1-8b-instruct:free", # Rapide et fiable
        "mistralai/mistral-7b-instruct:free",    # Le champion français
        "qwen/qwen-2-7b-instruct:free"
    ]

def appel_oracle_securise(system_prompt, user_prompt):
    client = openai.OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key="METTRE CLÉ API ICI(entre apostrophe)",
    )

    # On tente chaque modèle l'un après l'autre
    for model_id in MODELES_PRIORITAIRES:
        try:
            response = client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={ "type": "json_object" },
                timeout=10 # On n'attend pas plus de 10 sec par modèle
            )
            # Si on arrive ici, c'est que ça a marché !
            return json.loads(response.choices[0].message.content)
        
        except Exception as e:
            # Si erreur, on affiche un petit message discret en console et on continue
            print(f"⚠️ Échec avec {model_id}: {e}")
            continue 
    
    # Si on arrive au bout de la liste sans succès
    return {"error": "L'Oracle est fatigué, réessaie plus tard."}

def generer_suggestion_quete(df_user, domaine_id, intensite, prompt_joueur=""):
    # 1. Préparation du contexte métier
    diff_monde = st.session_state.get('difficulte', 'Normal')
    label_domaine = df_user[df_user['ID'] == domaine_id]['Label'].values[0]
    
    # Résumé des forces/faiblesses pour guider l'IA
    top_competence = df_user.loc[df_user['XP'].idxmax()]['Label']
    stats_string = f"Force : {top_competence}, Domaine actuel : {label_domaine}"

    # 2. Le Prompt Système (L'identité)
    system_prompt = f"""Tu es l'Oracle, une IA de productivité avancée qui utilise une interface de jeu. 
    Ton but : Transformer des intentions floues en quêtes concrètes, mesurables et chronométrées.

    CONTEXTE DU MONDE
    - Difficulté Globale : {diff_monde} (Si 'Difficile', augmente les répétitions/durées).
    - État du Héros : {stats_string}
    - Quête à forger : Intensité '{intensite}'

    RÈGLES DE FORGE (CRUCIAL) :
    1. ZÉRO MYSTÈRE : L'objectif doit être limpide. Pas de "bord du lac", mais des "minutes", "pages", "pompes" ou "lignes de code".
    2. STRUCTURE DU TITRE : [Verbe d'action] + [Quantité] + [Objet]. 
    Exemple : "Sprint de 20min", "Lecture de 15 pages", "Série de 30 Flexions".
    3. ÉCHELLE D'INTENSITÉ '{intensite}':
    - 'Petite' : Effort flash (< 15 min). Récompense : 50-100 XP.
    - 'Soutenue' : Effort focalisé (30 min - 1h30). Récompense : 80-230 XP.
    - 'Épique' : Défi majeur (> 2h ou sortie de zone de confort). Récompense : 300-600 XP.

    INSTRUCTIONS :
    - Domaine : {label_domaine}.
    - Inspiration : "{prompt_joueur}".
    - Style : Moderne et direct.
    - Format Titre : [Verbe d'action] + [Quantité] + [Objet].
    - Touches Fantaisistes : Utilise des termes comme "Manuscrit" (pour livre), "Rituel" (pour routine), "Artefact" (pour outil), "Mana" (pour énergie).

    FORMAT DE RÉPONSE (JSON STRICT) :
    {{
        "titre": "Action précise + Quantité",
        "xp_base": nombre_entier,
        "explication": "Une phrase courte : 1 conseil moderne + 1 métaphore guerrière."
    }}"""

    # 3. Le Prompt Utilisateur (La demande)
    user_prompt = f"L'aventurier a une idée : '{prompt_joueur}'. Forge son destin pour le domaine {label_domaine}."
    if not prompt_joueur:
        user_prompt = f"L'aventurier attend un signe pour le domaine {label_domaine}. Surprends-le."

    return appel_oracle_securise(system_prompt, user_prompt)

def demander_conseil_oracle(contexte_hero, question_utilisateur):
    """
    Donne des conseils stratégiques basés sur le contexte complet (XP + Oubli + Global).
    """
    system_prompt = f"""
    Tu es le Sage Mentor de l'Aventurier. 
    
    VOICI L'ÉTAT DE SON ÂME (CONTEXTE) :
    {contexte_hero}
    
    TES MISSIONS :
    1. Analyse les alertes d'Oubli : Si une compétence s'efface, rappelle-lui son importance.
    2. Regarde le Niveau Global : S'il est bas par rapport aux forces, pousse à la diversification.
    3. Réponds avec sagesse, mystère et bienveillance (ton médiéval-fantastique moderne).

    ALERTE ATROPHIE : Si tu vois des domaines avec une fraîcheur < 50%, 
    prends un ton plus grave. Dis au joueur que son héritage se dissipe 
    dans les brumes de l'oubli et qu'il doit agir MAINTENANT pour stopper l'hémorragie d'XP.

    FORMAT DE RÉPONSE (JSON STRICT) :
    {{
        "reponse": "Ton conseil ici (max 3 phrases)",
        "suggestion_domaine": "Le nom exact du domaine à travailler en priorité"
    }}
    """
    
    return appel_oracle_securise(system_prompt, question_utilisateur)

def preparer_contexte_ia(df, username):
    # 1. On ignore META
    df_game = df[(df['Parent'] != 'META') & (df['ID'] != 'GLO')].copy()
    
    # 2. On identifie le point le plus faible (hors Global)
    plus_faible = df_game.loc[df_game['XP'].idxmin()]
    
    # 3. On regarde si Global est à la traîne (ex: si aucun domaine n'est > LVL 10)
    lvl_global = get_global_level(username)

    contexte = f"--- ÉTAT DE L'AVENTURIER ---\n"
    contexte += f"Niveau Global (Aura) : {lvl_global}/100\n"
    contexte += f"""
    - Point Critique : {plus_faible['Label']} (Niveau {get_level(plus_faible['XP'])}).
    """

    if not df_game.empty:
        max_xp_domaine = df_game['XP'].max()
        if max_xp_domaine > (lvl_global * 50): # Seuil arbitraire pour détecter un déséquilibre
            contexte += "ATTENTION : Le héros est trop spécialisé. Son Aura globale (Niveau Global) est faible.\n"
    
    # On ajoute les domaines qui s'oublient
    for _, row in df_game.iterrows():
        f = calculer_fraicheur(row['Derniere_Activite'])
        if f < 40:
            contexte += f"\n- Alerte Oubli : La compétence '{row['Label']}' est en train de s'effacer ({f}%)."

    return contexte