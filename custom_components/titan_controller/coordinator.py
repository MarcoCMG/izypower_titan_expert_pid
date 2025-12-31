from datetime import timedelta
import logging
from collections import deque

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, REGULATION_PROFILES

_LOGGER = logging.getLogger(__name__)

class TitanPIDCoordinator(DataUpdateCoordinator):
    """Cerveau de la régulation PID Titan avec paramètres optimisés."""

    def __init__(self, hass, entry, shelly_entity_id):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=1),
        )
        self.entry = entry
        self.shelly_entity_id = shelly_entity_id
        self.titan_device_id = None  # Injecté par __init__.py
        self.enabled = False         # Piloté par le switch
        
        # Chargement du profil de stabilisation idéal
        # p: 0.3, i: 0.05, d: 0.1, target: -5, deadband: 20
        self.mode = entry.options.get("mode_regulation", entry.data.get("mode_regulation", "Performance (Zéro Conso)"))
        self.profile = REGULATION_PROFILES.get(self.mode)
        
        self.last_consigne = 0
        self.integral = 0
        self.last_error = 0
        self.history = deque(maxlen=self.profile["window"])

    async def _async_update_data(self):
        """Moteur de calcul et envoi des ordres de puissance."""
        
        # 1. Récupération de la mesure
        state = self.hass.states.get(self.shelly_entity_id)
        if not state or state.state in ["unknown", "unavailable"]:
            raise UpdateFailed(f"Capteur Shelly {self.shelly_entity_id} indisponible")

        try:
            conso_actuelle = float(state.state)
        except ValueError:
            raise UpdateFailed(f"Valeur non numérique: {state.state}")

        # 2. Calcul de l'erreur (Cible idéale: -5W)
        erreur = conso_actuelle - self.profile["target"]

        # 3. Sortie anticipée si désactivé ou dans la Deadband (20W)
        if not self.enabled or abs(erreur) < self.profile["deadband"]:
            return self._format_data(erreur)

        # 4. Lissage (Fenêtre: 8)
        self.history.append(erreur)
        erreur_lissee = sum(self.history) / len(self.history)
        
        # 5. PID avec Anti-Windup (Limite Intégrale: 200)
        limit_i = self.profile["i_limit"]
        self.integral = max(-limit_i, min(limit_i, self.integral + erreur_lissee))
        delta_erreur = erreur_lissee - self.last_error

        # Facteurs: P=0.3, I=0.05, D=0.1
        correction = (
            (self.profile["p"] * erreur_lissee) +
            (self.profile["i"] * self.integral) +
            (self.profile["d"] * delta_erreur)
        )

        # 6. Asymétrie (Max Up: 2500 / Max Down: 400)
        max_step = self.profile["max_up"] if correction > 0 else self.profile["max_down"]
        correction_finale = max(-max_step, min(max_step, correction))

        # 7. Calcul Consigne et Bornage de sécurité (4800W max)
        # On additionne la correction à l'ancienne consigne pour la continuité
        nouvelle_consigne = max(-4800, min(4800, self.last_consigne + correction_finale))
        self.last_consigne = nouvelle_consigne
        self.last_error = erreur_lissee

        # 8. ENVOI DE L'ORDRE PHYSIQUE
        await self._send_titan_command(nouvelle_consigne)

        return self._format_data(erreur)

    async def _send_titan_command(self, power):
        """Communique avec les services de la batterie Titan."""
        if not self.titan_device_id:
            return

        # Détermine si on doit charger ou décharger
        service = "discharge" if power >= 0 else "charge"
        power_val = abs(int(power))

        try:
            await self.hass.services.async_call(
                "izypower_titan_private", 
                service,
                {
                    "device_id": self.titan_device_id,
                    "power": power_val,
                    "soc_limit": 10 if service == "discharge" else 100
                }
            )
        except Exception as e:
            _LOGGER.error("Erreur lors de l'envoi de l'ordre au Titan: %s", e)

    def _format_data(self, erreur):
        """Prépare les données pour les capteurs sensor.py."""
        return {
            "consigne": round(self.last_consigne, 1),
            "integral": round(self.integral, 2),
            "erreur": round(erreur, 1),
            "mode": self.mode
        }
