"""Constantes pour l'intégration Titan Expert PID."""

DOMAIN = "titan_controller"

# Noms des profils affichés dans l'interface
PROFIL_ECO = "Eco (Anti-Injection)"
PROFIL_BALANCED = "Équilibré"
PROFIL_PERF = "Performance (Zéro Conso)"

# Configuration technique des profils (Version optimisée 31/12)
# p : Force de réaction
# i : Précision (Intégrale)
# d : Amortissement
# target : Puissance réseau visée (négatif = injection)
# max_up : Vitesse de montée (décharge batterie) - Réactivité aux charges
# max_down : Vitesse de descente (arrêt décharge) - Stabilité post-pic
# deadband : Zone morte en Watts pour ignorer le bruit de mesure
# window : Nombre de mesures pour la moyenne glissante
# i_limit : Bornes anti-windup pour l'intégrale [-valeur, +valeur]
REGULATION_PROFILES = {
    PROFIL_ECO: {
        "p": 0.3, 
        "i": 0.04, 
        "d": 0.1, 
        "target": 15,    
        "max_up": 600,   
        "max_down": 2500,
        "deadband": 25,
        "window": 10,
        "i_limit": 150
    },
    PROFIL_BALANCED: {
        "p": 0.4, 
        "i": 0.05, 
        "d": 0.1, 
        "target": 0,     
        "max_up": 1500,  
        "max_down": 800,
        "deadband": 20,
        "window": 8,
        "i_limit": 200
    },
    PROFIL_PERF: {
        "p": 0.3,        # Paramètre validé pour éviter le pompage
        "i": 0.05,       # Paramètre validé
        "d": 0.1,        # Paramètre validé
        "target": -5,    # Ta cible idéale pour le 0 conso sans gaspillage
        "max_up": 2500,  # Capacité maximale pour couvrir les gros appareils
        "max_down": 400, # Frein à la descente pour la stabilité
        "deadband": 20,  # Pour stabiliser la ligne à basse conso
        "window": 8,     # Filtrage validé sur tes graphiques
        "i_limit": 200   # Anti-windup pour retour au calme rapide
    }
}

# Liste pour le menu déroulant du config_flow
CONF_MODE_REGULATION = "mode_regulation"
MODES_LIST = [PROFIL_ECO, PROFIL_BALANCED, PROFIL_PERF]
