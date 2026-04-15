import streamlit as st
import pandas as pd
import os
import math
from datetime import date, datetime

def charger_donnees_user(username):
    filename = f"data/user_data/data_{username}.csv"

    # 1. TENTATIVE DE CHARGEMENT
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        try:
            df = pd.read_csv(filename)

            # SÉCURITÉ : Ajouter la colonne d'activité si elle manque (pour les anciens comptes)
            if 'Derniere_Activite' not in df.columns:
                df['Derniere_Activite'] = date.today().strftime("%Y-%m-%d")
                df.to_csv(filename, index=False)

            return df
        except Exception:
            # Si le fichier est illisible, on va en créer un nouveau plus bas
            pass

    # 2. CRÉATION D'UN NOUVEAU FICHIER (si absent ou corrompu)
    # On définit directement TOUTES les colonnes nécessaires ici
    columns = ['ID', 'Parent', 'Label', 'XP', 'Derniere_Activite']
    df = pd.DataFrame(columns=columns)

    # Ajout du nœud Global par défaut
    nouvelle_ligne = pd.DataFrame([{
        'ID': 'GLO', 
        'Label': '🌐Global', 
        'Parent': '', 
        'XP': 100,
        'Derniere_Activite': date.today().strftime("%Y-%m-%d")
    }])
    df = pd.concat([df, nouvelle_ligne], ignore_index=True)

    df.to_csv(filename, index=False)
    return df

def sauvegarder_donnees_user(username, edited_df):
    """Sauvegarde le CSV perso dans le dossier data_users."""
    filename = os.path.join(f"data/user_data/data_{username}.csv")
    edited_df.to_csv(filename, index=False)

def securite_page():
    """Vérifie si l'utilisateur est loggé (nommée 'username' pour la cohérence)."""
    if "username" not in st.session_state or not st.session_state.logged_in:
        st.error("🚫 Accès refusé. Veuillez vous connecter.")
        st.stop()

def est_domaine_principal(df, node_id):
    """
    Vérifie si le node_id est un parent qui n'a que des feuilles 
    (compétences sans enfants) comme descendants directs.
    """
    enfants = df[df['Parent'] == node_id]['ID'].tolist()
    if not enfants:
        return False
    # Vérifie si l'un des enfants est lui-même un parent
    a_des_petits_enfants = df['Parent'].isin(enfants).any()
    return not a_des_petits_enfants

def get_level(xp):
    """Calcule le niveau (max 100) basé sur l'XP."""
    if xp <= 0: return 0
    lvl = math.floor(math.sqrt(xp / 100))
    return min(100, lvl)

def get_xp_for_level(level):
    """Calcule l'XP totale nécessaire pour atteindre un niveau donné."""
    return 100 * (level ** 2)

def calculer_xp_noeud(df, node_id):
    """
    Calcule l'XP totale d'un nœud en additionnant son XP propre 
    ET celle de tous ses descendants (enfants, petits-enfants, etc.)
    """
    # 1. Sécurité de base
    if node_id is None or node_id == "" or df.empty:
        return 0

    # 2. On récupère l'XP propre du nœud actuel
    # On s'assure que c'est un nombre pour éviter les erreurs de calcul
    mask_soi = df['ID'] == node_id
    xp_propre = 0
    if mask_soi.any():
        xp_propre = pd.to_numeric(df.loc[mask_soi, 'XP'].iloc[0], errors='coerce') or 0

    # 3. RÉCURSIVITÉ : On cherche les enfants directs
    enfants = df[df['Parent'] == node_id]

    xp_enfants = 0
    for _, row_enfant in enfants.iterrows():
        # Appel récursif : la fonction s'appelle elle-même pour chaque enfant
        xp_enfants += calculer_xp_noeud(df, row_enfant['ID'])

    return xp_propre + xp_enfants


def obtenir_stats_completes(df, node_id):
    """
    Retourne un dictionnaire avec toutes les infos pour un bureau :
    XP actuelle, Niveau, XP pour le prochain niveau, % de progression.
    """
    xp_actuelle = calculer_xp_noeud(df, node_id)
    lvl = get_level(xp_actuelle)

    if lvl >= 100:
        return {"lvl": 100, "xp": xp_actuelle, "next_xp": 0, "pct": 100}

    xp_palier_actuel = get_xp_for_level(lvl)
    xp_palier_suivant = get_xp_for_level(lvl + 1)

    # Calcul du pourcentage de progression dans le niveau actuel
    progression_dans_lvl = xp_actuelle - xp_palier_actuel
    distance_entre_paliers = xp_palier_suivant - xp_palier_actuel
    pct = (progression_dans_lvl / distance_entre_paliers) * 100

    return {
        "lvl": lvl,
        "xp": xp_actuelle,
        "next_xp": xp_palier_suivant,
        "pct": round(pct, 1)
    }

def charger_quetes_user(username):
    filename = f"data/quest_data/quests_{username}.csv"
    columns = ["ID_Quete", "ID_Competence", "Titre", "XP_Recompense", "Statut", "Type", "Date_Creation", "Date_Completion"]

    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        df = pd.read_csv(filename)
        # --- NETTOYAGE : Supprime les colonnes "Unnamed" ---
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        # S'assurer que toutes les colonnes vitales sont là
        for col in columns:
            if col not in df.columns:
                df[col] = ""
        return df
    else:
        df = pd.DataFrame(columns=columns)
        df.to_csv(filename, index=False)
        return df

def ajouter_xp(username, skill_id, montant_xp):
    df = charger_donnees_user(username)
    if skill_id in df['ID'].values:
        # SÉCURITÉ ANTI-BUG : On force le type numérique
        df['XP'] = pd.to_numeric(df['XP'], errors='coerce').fillna(0)
        df.loc[df['ID'] == skill_id, 'XP'] += int(montant_xp)
        df.loc[df['ID'] == skill_id, 'Derniere_Activite'] = date.today().strftime("%Y-%m-%d")
        df.to_csv(f"data/user_data/data_{username}.csv", index=False)
        return True
    return False

def creer_quete(username, comp_id, titre, xp, type_quete="Secondaire"):
    df = charger_quetes_user(username)

    # Vérification Quête Principale
    if type_quete == "Principale":
        existe = df[(df['ID_Competence'] == comp_id) & (df['Statut'] == "En cours") & (df['Type'] == "Principale")]
        if not existe.empty:
            return False, "⚠️ Une quête principale est déjà en cours !"

    nouveau_id = f"Q{len(df) + 2}"

    # Nouvelle ligne propre
    nouvelle_ligne = pd.DataFrame([{
        "ID_Quete": nouveau_id,
        "ID_Competence": comp_id,
        "Titre": titre,
        "XP_Recompense": int(xp),
        "Statut": "En cours",
        "Type": type_quete,
        "Date_Creation": date.today().strftime("%d/%m/%Y"),
        "Date_Completion": ""
    }])

    df = pd.concat([df, nouvelle_ligne], ignore_index=True)
    df.to_csv(f"data/quest_data/quests_{username}.csv", index=False)
    return True, "La quête a été forgée !"

def valider_quete(username, id_quete):
    df_q = charger_quetes_user(username)
    mask = df_q['ID_Quete'] == id_quete

    if mask.any():
        idx = df_q.index[mask][0]
        df_q.at[idx, 'Statut'] = "Terminée"
        df_q.at[idx, 'Date_Completion'] = date.today().strftime("%d/%m/%Y")

        id_comp = df_q.at[idx, 'ID_Competence']
        xp = int(df_q.at[idx, 'XP_Recompense'])

        df_q.to_csv(f"data/quest_data/quests_{username}.csv", index=False)
        return ajouter_xp(username, id_comp, xp)
    return False

def supprimer_quete(username, quete_id):
    filename = f"data/quest_data/quests_{username}.csv"
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        # On garde tout sauf la quête visée
        df = df[df['ID_Quete'] != quete_id]
        df.to_csv(filename, index=False)
        return True
    return False

def creer_domaine(username, parent, label):
    df = charger_donnees_user(username)

    # 1. Génération d'un ID unique (3 lettres + un chiffre si doublon)
    base_id = label[:3].upper()
    nouveau_id = base_id
    compteur = 1
    while nouveau_id in df['ID'].values:
        nouveau_id = f"{base_id}{compteur}"
        compteur += 1

    # 2. Création de la ligne avec XP à 0
    nouvelle_ligne = {
        "ID": nouveau_id,
        "Parent": parent if parent else "GLO", # "GLO" par défaut si vide
        "Label": label,
        "XP": 0
    }

    # 3. Ajout et sauvegarde
    df = pd.concat([df, pd.DataFrame([nouvelle_ligne])], ignore_index=True)
    df.to_csv(f"data/user_data/data_{username}.csv", index=False)
    return True

def supprimer_domaine(username, id_a_supprimer):
    df = charger_donnees_user(username)

    # On vérifie si ce domaine est le parent d'autres éléments
    if id_a_supprimer in df['Parent'].values:
        return False, "Ce domaine contient des sous-compétences. Supprime-les d'abord !"

    # On filtre pour garder tout SAUF celui qu'on veut supprimer
    df = df[df['ID'] != id_a_supprimer]
    df.to_csv(f"data/user_data/data_{username}.csv", index=False)
    return True, "Domaine supprimé avec succès."

def get_global_level(username):
    df = charger_donnees_user(username)
    if df.empty: return 0

    # ÉTAPE CRUCIALE : On ignore les lignes de paramètres (META)
    df_game = df[df['Parent'] != 'META'].copy() 

    if df_game.empty: return 0

    df_game['XP'] = pd.to_numeric(df_game['XP'], errors='coerce').fillna(0)
    liste_parents = df_game['Parent'].unique()
    df_feuilles = df_game[~df_game['ID'].isin(liste_parents)]

    somme_des_niveaux = df_feuilles['XP'].apply(get_level).sum()

    # Formule : $$Niveau = \frac{\sum Levels}{20}$$
    niveau_global = somme_des_niveaux / 20
    return max(1, min(100, math.floor(niveau_global)))

def preparer_donnees_graphique(username, periode="Semaine"):
    df_q = charger_quetes_user(username)

    # 1. On ne garde que les quêtes terminées
    df_terminees = df_q[df_q['Statut'] == "Terminée"].copy()

    if df_terminees.empty:
        return pd.DataFrame(columns=['Date', 'XP'])

    # 2. Nettoyage de l'XP et des Dates
    df_terminees['XP_Recompense'] = pd.to_numeric(df_terminees['XP_Recompense'], errors='coerce').fillna(0)

    # Sécurité : Si Date_Completion est vide, on prend Date_Creation (pour l'historique)
    df_terminees['Date_Completion'] = df_terminees['Date_Completion'].fillna(df_terminees['Date_Creation'])
    df_terminees.loc[df_terminees['Date_Completion'] == "", 'Date_Completion'] = df_terminees['Date_Creation']

    # Conversion propre (dayfirst=True pour ton format DD/MM/YYYY)
    df_terminees['Date_Completion'] = pd.to_datetime(df_terminees['Date_Completion'], dayfirst=True, errors='coerce')
    df_terminees = df_terminees.dropna(subset=['Date_Completion'])

    # 3. Définition de la plage de dates
    aujourdhui = pd.Timestamp.now().normalize()
    jours_delta = 6 if periode == "Semaine" else 29 if periode == "Mois" else 364
    date_debut = aujourdhui - pd.Timedelta(days=jours_delta)

    # 4. On crée l'index complet pour boucher les trous (jours à 0 XP)
    idx = pd.date_range(date_debut, aujourdhui)

    # 5. Groupement par Date de Complétion
    stats_xp = df_terminees.groupby('Date_Completion')['XP_Recompense'].sum()

    # 6. Reindexation pour avoir tous les jours affichés
    stats_xp = stats_xp.reindex(idx, fill_value=0).reset_index()
    stats_xp.columns = ['Date', 'XP']

    return stats_xp

def obtenir_difficulte_jeu(username):
    df = charger_donnees_user(username)
    # On cherche une ligne spéciale avec l'ID 'SETTING_DIFF'
    ligne = df[df['ID'] == 'SETTING_DIFF']
    if not ligne.empty:
        return ligne.iloc[0]['Label'] # On stocke la valeur dans 'Label'
    return "Normal" # Par défaut

def sauvegarder_difficulte_jeu(username, nouvelle_diff):
    df = charger_donnees_user(username)

    if 'SETTING_DIFF' in df['ID'].values:
        df.loc[df['ID'] == 'SETTING_DIFF', 'Label'] = nouvelle_diff
    else:
        # On s'assure que XP est bien 0 et Parent est META
        nouvelle_ligne = pd.DataFrame([{
            'ID': 'SETTING_DIFF', 
            'Label': nouvelle_diff, 
            'Parent': 'META', 
            'XP': 0
        }])
        df = pd.concat([df, nouvelle_ligne], ignore_index=True)

    sauvegarder_donnees_user(username, df)

def obtenir_titre_rang(niveau):
    if niveau < 10: return "Vagabond"
    if niveau < 20: return "Apprenti Aventurier"
    if niveau < 30: return "Médaillé d'or"
    if niveau < 40: return "Explorateur Pro"
    if niveau < 50: return "Tailleur de Saphir"
    if niveau < 60: return "Aventurier Confirmé"
    if niveau < 70: return "Visionnaire"
    if niveau < 80: return "Maître Assistant"
    if niveau < 90: return "Chercheur de Diamant"
    if niveau < 100: return "Demi-Dieu"
    return "Légende Vivante"

def calculer_fraicheur(date_str):
    if not date_str or pd.isna(date_str) or date_str == "": 
        return 100 # C'est ici que ça peut bloquer si la date est mal lue

    try:
        # Tentative avec le format standard
        derniere = datetime.strptime(str(date_str), "%Y-%m-%d").date()
        jours_ecoules = (date.today() - derniere).days

        if jours_ecoules <= 7: return 100
        fraicheur = max(0, 100 - ((jours_ecoules - 7) * 4.34)) 
        return round(fraicheur)

    except Exception as e:
        # Si ça plante, on veut voir l'erreur dans Streamlit !
        st.error(f"Erreur Date : {e} sur la valeur '{date_str}'")
        return 100

def obtenir_date_fraicheur_reelle(df_user, domaine_id):
    """
    Va chercher la date la plus récente de TOUS les descendants 
    (enfants, petits-enfants, etc.) de manière récursive.
    """
    # 1. On récupère la date de la ligne actuelle
    selection = df_user[df_user['ID'] == domaine_id]
    if selection.empty:
        return ""

    date_max = pd.to_datetime(selection.iloc[0].get('Derniere_Activite', ""), errors='coerce')

    # 2. On récupère TOUS les descendants (on descend dans l'arbre)
    def trouver_tous_descendants(parent_id):
        enfants = df_user[df_user['Parent'] == parent_id]['ID'].tolist()
        descendants = list(enfants)
        for enfant_id in enfants:
            descendants.extend(trouver_tous_descendants(enfant_id))
        return descendants

    tous_ids = trouver_tous_descendants(domaine_id)

    if tous_ids:
        # On récupère les dates de tous les descendants
        df_descendants = df_user[df_user['ID'].isin(tous_ids)]
        dates_desc = pd.to_datetime(df_descendants['Derniere_Activite'], errors='coerce').dropna()

        if not dates_desc.empty:
            # On compare la date du parent avec la plus récente des descendants
            date_max_desc = dates_desc.max()
            if pd.isna(date_max) or date_max_desc > date_max:
                date_max = date_max_desc

    return date_max.strftime("%Y-%m-%d") if pd.notna(date_max) else ""

def appliquer_atrophie(username):
    df = charger_donnees_user(username)
    seuil_grace = 14
    taux_perte = 0.001 
    modifie = False

    mask_jeu = (df['Parent'] != 'META') & (df['ID'] != 'GLO')

    for idx, row in df[mask_jeu].iterrows():
        valeur_date = row['Derniere_Activite']
        if pd.isna(valeur_date) or valeur_date == "": continue

        # --- ASTUCE DE RÉPARATION ---
        try:
            # On tente le format 4 chiffres (2026)
            derniere = datetime.strptime(str(valeur_date), "%Y-%m-%d").date()
        except ValueError:
            # Si ça rate, c'est sûrement l'ancien format 2 chiffres (26)
            # On le répare à la volée !
            derniere = datetime.strptime(str(valeur_date), "%y-%m-%d").date()
            df.at[idx, 'Derniere_Activite'] = derniere.strftime("%Y-%m-%d")
            modifie = True

        # --- RESTE DU CALCUL ---
        jours_inactifs = (date.today() - derniere).days
        if jours_inactifs > seuil_grace:
            jours_a_punir = jours_inactifs - seuil_grace
            xp_actuelle = row['XP']

            # Calcul de la perte : XP * (0.1% * jours)
            perte = xp_actuelle * (taux_perte * jours_a_punir)

            if perte > 0:
                # On applique la perte sans descendre en dessous de 0
                df.at[idx, 'XP'] = max(0, xp_actuelle - perte)
                modifie = True

    if modifie:
        df.to_csv(f"data/user_data/data_{username}.csv", index=False)
        return True
    return False

def preparer_donnees_echarts_bureau(username, domaine_id, periode="Semaine"):
    df_user = charger_donnees_user(username)
    df_q = charger_quetes_user(username)

    sous_domaines = df_user[df_user['Parent'] == domaine_id]
    ids_interet = sous_domaines['ID'].tolist() + [domaine_id]

    # Filtrage quêtes terminées
    df_t = df_q[(df_q['Statut'] == "Terminée") & (df_q['ID_Competence'].isin(ids_interet))].copy()

    if df_t.empty:
        return [], [], []

    # Nettoyage des types
    df_t['XP_Recompense'] = pd.to_numeric(df_t['XP_Recompense'], errors='coerce').fillna(0)
    df_t['Date_Completion'] = pd.to_datetime(df_t['Date_Completion'], dayfirst=True, errors='coerce')
    df_t = df_t.dropna(subset=['Date_Completion'])

    # Axe X
    jours = 7 if periode == "Semaine" else 30
    dates_axe = [(pd.Timestamp.now().normalize() - pd.Timedelta(days=i)).strftime("%d/%m") for i in range(jours)][::-1]

    series_data = []
    for _, enfant in sous_domaines.iterrows():
        valeurs = []
        for d_str in dates_axe:
            mask = (df_t['Date_Completion'].dt.strftime("%d/%m") == d_str) & (df_t['ID_Competence'] == enfant['ID'])
            valeurs.append(int(df_t[mask]['XP_Recompense'].sum()))

        if sum(valeurs) > 0:
            series_data.append({"name": enfant['Label'], "type": "line", "smooth": True, "data": valeurs})

    return dates_axe, series_data, [s['name'] for s in series_data]
Footer
© 2026 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Community
Docs
Contact
Manage cookies
Do not share my personal information
