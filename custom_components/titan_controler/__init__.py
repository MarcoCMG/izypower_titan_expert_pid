import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Configuration de l'intégration via l'UI."""
    
    # Récupération des paramètres configurés
    shelly_entity = entry.data.get("shelly_entity")
    titan_id = entry.data.get("titan_device_id")
    p_factor = entry.data.get("facteur_p", 0.7)
    i_factor = entry.data.get("facteur_i", 0.2)

    # Stockage de l'état interne de la régulation
    class TitanState:
        def __init__(self):
            self.integral = 0
            self.history = []
            self.last_consigne = 0
            self.enabled = True  # État piloté par le switch.py

    state = TitanState()
    # On rend l'objet state accessible aux autres fichiers (comme switch.py)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = state

    @callback
    async def _async_on_power_change(event):
        """Boucle de régulation PI déclenchée à chaque changement du Shelly."""
        if not state.enabled:
            return

        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ["unknown", "unavailable", "none"]:
            return

        try:
            puissance_brute = float(new_state.state)
            
            # 1. Filtrage (Moyenne glissante sur 2 points)
            state.history.append(puissance_brute)
            if len(state.history) > 2:
                state.history.pop(0)
            
            puissance_filtree = sum(state.history) / len(state.history)
            
            # 2. Calcul de l'erreur (Cible = 0W)
            erreur = puissance_filtree - 0 
            
            # 3. Calcul de l'intégrale avec clampage (Anti-windup)
            state.integral = max(-500, min(500, state.integral + erreur))
            
            # 4. Calcul de la correction brute
            correction_brute = (p_factor * erreur) + (i_factor * state.integral)
            
            # 5. Bridage de la vitesse (Max Step asymétrique)
            # 2500 si erreur < 0 (besoin de puissance), 600 si erreur > 0 (anti-injection)
            max_step = 2500 if erreur < 0 else 600
            correction_bridee = max(-max_step, min(max_step, correction_brute))
            
            # 6. Calcul de la nouvelle consigne finale
            nouvelle_consigne = max(-4800, min(4800, int(state.last_consigne + correction_bridee)))
            state.last_consigne = nouvelle_consigne

            # 7. Envoi des ordres si hors zone morte (deadband de 8W)
            if abs(puissance_filtree) > 8:
                if nouvelle_consigne > 0:
                    # Mode Décharge
                    await hass.services.async_call(
                        "izypower_titan_private", "discharge",
                        {
                            "device_id": titan_id, 
                            "power": nouvelle_consigne, 
                            "soc_limit": 10
                        }
                    )
                elif nouvelle_consigne < 0:
                    # Mode Charge
                    await hass.services.async_call(
                        "izypower_titan_private", "charge",
                        {
                            "device_id": titan_id, 
                            "power": abs(nouvelle_consigne), 
                            "soc_limit": 100
                        }
                    )
        
        except ValueError:
            _LOGGER.warning(f"Valeur non numérique reçue du Shelly: {new_state.state}")
        except Exception as e:
            _LOGGER.error(f"Erreur critique régulation Titan: {e}")

    # Enregistrement du trigger (écouteur d'état)
    # entry.async_on_unload assure que l'écouteur s'arrête si on supprime l'intégration
    entry.async_on_unload(
        async_track_state_change_event(hass, shelly_entity, _async_on_power_change)
    )

    # Chargement de la plateforme switch
    await hass.config_entries.async_forward_entry_setups(entry, ["switch"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Déchargement de l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["switch"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok