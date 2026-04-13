import streamlit as st
from PIL import Image

mx_reg = -17
my_reg = 164
spx_reg = 52
spy_reg = 59

CONFIG_TIERS = {
    # Tier: { "fichier": "nom", "taille": pixels, "cols": nombre }
    0: {"file": "blason_tier0.png", "w": 350, "cols": 5, "m_x": mx_reg, "m_y": my_reg, "sp_x": spx_reg, "sp_y": spy_reg}, # Tranche 1-9
    1: {"file": "blason_tier1.png", "w": 350, "cols": 5, "m_x": mx_reg, "m_y": my_reg, "sp_x": spx_reg, "sp_y": spy_reg}, # Tranche 10-19
    2: {"file": "blason_tier2.png", "w": 350, "cols": 5, "m_x": mx_reg, "m_y": my_reg, "sp_x": spx_reg, "sp_y": spy_reg}, # Tranche 20-29
    3: {"file": "blason_tier3.png", "w": 350, "cols": 5, "m_x": mx_reg, "m_y": my_reg, "sp_x": spx_reg, "sp_y": spy_reg}, # Tranche 30-39
    4: {"file": "blason_tier4.png", "w": 350, "cols": 5, "m_x": mx_reg, "m_y": my_reg, "sp_x": spx_reg, "sp_y": spy_reg}, # Tranche 40-49
    5: {"file": "blason_tier5.png", "w": 350, "cols": 5, "m_x": mx_reg, "m_y": my_reg, "sp_x": spx_reg, "sp_y": spy_reg}, # Tranche 50-59
    6: {"file": "blason_tier6.png", "w": 350, "cols": 5, "m_x": mx_reg, "m_y": my_reg, "sp_x": spx_reg, "sp_y": spy_reg}, # Tranche 60-69
    7: {"file": "blason_tier7.png", "w": 350, "cols": 5, "m_x": mx_reg, "m_y": my_reg, "sp_x": spx_reg, "sp_y": spy_reg}, # Tranche 70-79
    8: {"file": "blason_tier8.png", "w": 350, "cols": 5, "m_x": mx_reg, "m_y": my_reg, "sp_x": spx_reg, "sp_y": spy_reg}, # Tranche 80-89
    9: {"file": "blason_tier9.png", "w": 350, "cols": 5, "m_x": 2, "m_y": 172, "sp_x": 43, "sp_y": 48}, # Tranche 90-99
    10: {"file": "blason_tier10.png", "w": 800, "cols": 1, "m_x": 560, "m_y": 165, "sp_x": 0, "sp_y": 0} # Tranche 100 (plus gros !)
}

def get_rang_image(niveau):
    niveau = max(1, niveau)
    if niveau >= 100:
        tier_id = 10       # On force l'accès au Tier 10
        index_local = 0    # On prend le 1er blason (l'unique) du fichier 100
    else:
        # Formule normale pour tous les autres niveaux (1 à 99)
        tier_id = (niveau) // 10
        index_local = (niveau) % 10
    
    conf = CONFIG_TIERS[tier_id]
    img = Image.open(f"sprite/{conf['file']}")
    
    col = index_local % conf['cols']
    row = index_local // conf['cols']

    left = conf['m_x'] + (col * (conf['w'] + conf['sp_x']))
    top = conf['m_y'] + (row * (conf['w'] + conf['sp_y']))
    
    right = left + conf['w']
    bottom = top + conf['w']

    return img.crop((left, top, right, bottom))