from datetime import timedelta
import logging
from collections import deque

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, REGULATION_PROFILES

_LOGGER = logging.getLogger(__name__)

class TitanPIDCoordinator(DataUpdateCoordinator):
    """Cerveau de la régulation PID Titan."""

    def __init__(self, hass, entry, shelly_entity_id):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=1), # Fréquence de calcul fixe (1s)
        )
        self.entry = entry
        self.shelly_entity_id = shelly_entity_id
        
        # Sélection du profil et chargement des constantes validées
        self.mode = entry.data.get("mode_regulation", "Performance (Zéro Conso)")
        self.profile = REGULATION_PROFILES.get(self.mode)
        
        # Initialisation des variables PID
        self.last_consigne = 0
        self.integral = 0
        self.last_error = 0
        self.history = deque(maxlen=self.profile["window"]) # Moyenne glissante optimisée

    async def _async_update_data(self):
        """Moteur de calcul exécuté à chaque seconde."""
        
        # 1. Récupération de la mesure de consommation
        state = self.hass.states.get(self.shelly_entity_id)
        if not state or state.state in ["unknown", "unavailable"]:
            raise UpdateFailed(f"Capteur Shelly {self.shelly_entity_id} indisponible")

        try:
            conso_actuelle = float(state.state)
        except ValueError:
            raise UpdateFailed(f"Valeur non numérique reçue: {state.state}")

        # 2. Calcul de l'erreur brute par rapport à la cible
        # Target: -5W (pour le profil PERF)
        erreur = conso_actuelle - self.profile["target"]

        # 3. Application de la Deadband (Zone morte) pour la stabilité
        # Si l'erreur est < 20W, on fige la consigne pour éviter les oscillations
        if abs(erreur) < self.profile["deadband"]:
            return {
                "consigne": self.last_consigne,
                "integral": self.integral,
                "erreur": erreur,
                "mode": self.mode
            }

        # 4. Lissage par moyenne glissante
        self.history.append(erreur)
        erreur_lissee = sum(self.history) / len(self.history)
        
        # 5. Calcul de l'intégrale avec Anti-Windup (Bornage)
        # Limite : [-200, 200] pour éviter l'effet d'inertie
        limit = self.profile["i_limit"]
        self.integral = max(-limit, min(limit, self.integral + erreur_lissee))

        # 6. Calcul de la dérivée (Amortissement)
        delta_erreur = erreur_lissee - self.last_error

        # 7. Formule PID finale
        # Utilise p: 0.3, i: 0.05, d: 0.1
        correction = (
            (self.profile["p"] * erreur_lissee) +
            (self.profile["i"] * self.integral) +
            (self.profile["d"] * delta_erreur)
        )

        # 8. Application de l'asymétrie (Vitesse de réaction)
        # max_up (montée): 2500W | max_down (descente): 400W
        max_step = self.profile["max_up"] if correction > 0 else self.profile["max_down"]
        correction_finale = max(-max_step, min(max_step, correction))

        # Mise à jour de la consigne et sauvegarde de l'état
        self.last_consigne = max(0, self.last_consigne + correction_finale)
        self.last_error = erreur_lissee

        return {
            "consigne": round(self.last_consigne, 1),
            "integral": round(self.integral, 2),
            "erreur": round(erreur, 1),
            "mode": self.mode
        }
