"""Constantes pour l'intégration Titan Expert PID."""

DOMAIN = "titan_controller"

# Noms des profils affichés dans l'interface
PROFIL_ECO = "Eco (Anti-Injection)"
PROFIL_BALANCED = "Équilibré"
PROFIL_PERF = "Performance (Zéro Conso)"

# Configuration technique des profils (Version 30/12)
# P : Force de réaction
# I : Précision (Intégrale)
# D : Amortissement (Dérivée pour stopper les oscillations)
# target : Puissance réseau visée (négatif = injection)
# max_up : Vitesse de montée (décharge batterie)
# max_down : Vitesse de descente (charge ou arrêt décharge)
REGULATION_PROFILES = {
    PROFIL_ECO: {
        "p": 0.4, 
        "i": 0.08, 
        "d": 0.15, 
        "target": 15,    # On garde une petite marge de conso
        "max_up": 600,   # Montée lente
        "max_down": 2500 # Descente rapide (anti-injection)
    },
    PROFIL_BALANCED: {
        "p": 0.6, 
        "i": 0.12, 
        "d": 0.2, 
        "target": 0,     # On vise le 0 parfait
        "max_up": 1200, 
        "max_down": 1200
    },
    PROFIL_PERF: {
        "p": 0.7, 
        "i": 0.15, 
        "d": 0.3, 
        "target": -25,   # On injecte un peu pour être sûr de ne rien consommer
        "max_up": 2500,  # Montée ultra-rapide (réactivité max)
        "max_down": 400  # Descente lente (on privilégie le maintien de puissance)
    }
}

# Liste pour le menu déroulant du config_flow
CONF_MODE_REGULATION = "mode_regulation"
MODES_LIST = [PROFIL_ECO, PROFIL_BALANCED, PROFIL_PERF]
