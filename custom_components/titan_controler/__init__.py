import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Configuration de l'intégration via l'UI."""
    
    # 1. Récupération des paramètres configurés
    shelly_entity = entry.data.get("shelly_entity")
    titan_id = entry.data.get("titan_device_id")
    p_factor = entry.data.get("facteur_p", 0.7)
    i_factor = entry.data.get("facteur_i", 0.2)

    # 2. Stockage de l'état interne de la régulation
    class TitanState:
        def __init__(self):
            self.integral = 0
            self.history = []
            self.last_consigne = 0
            self.enabled = True  # Piloté par switch.py

    state = TitanState()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = state

    # 3. CRÉATION DE L'APPAREIL (Indispensable pour l'affichage de la carte)
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Régulateur Titan Expert",
        manufacturer="IzyPower",
        model="Expert PID v1",
    )

    # 4. Boucle de régulation PI
    @callback
    async def _async_on_power_change(event):
        """Calcul et envoi des ordres à la batterie."""
        if not state.enabled:
            return

        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ["unknown", "unavailable", "none"]:
            return

        try:
            puissance_brute = float(new_state.state)
            
            # Filtrage (Moyenne glissante 2 points)
            state.history.append(puissance_brute)
            if len(state.history) > 2:
                state.history.pop(0)
            
            puissance_filtree = sum(state.history) / len(state.history)
            
            # Calcul de l'erreur (Cible = 0W)
            erreur = puissance_filtree - 0 
            
            # Calcul de l'intégrale (Anti-windup +/- 500)
            state.integral = max(-500, min(500, state.integral + erreur))
            
            # Calcul de la correction brute
            correction_brute = (p_factor * erreur) + (i_factor * state.integral)
            
            # Bridage de la vitesse (Max Step asymétrique)
            max_step = 2500 if erreur < 0 else 600
            correction_bridee = max(-max_step, min(max_step, correction_brute))
            
            # Nouvelle consigne finale
            nouvelle_consigne = max(-4800, min(4800, int(state.last_consigne + correction_bridee)))
            state.last_consigne = nouvelle_consigne

            # Envoi des ordres via le service izypower_titan_private
            if abs(puissance_filtree) > 8:
                if nouvelle_consigne > 0:
                    await hass.services.async_call(
                        "izypower_titan_private", "discharge",
                        {
                            "device_id": titan_id, 
                            "power": nouvelle_consigne, 
                            "soc_limit": 10
                        }
                    )
                elif nouvelle_consigne < 0:
                    await hass.services.async_call(
                        "izypower_titan_private", "charge",
                        {
                            "device_id": titan_id, 
                            "power": abs(nouvelle_consigne), 
                            "soc_limit": 100
                        }
                    )
        
        except ValueError:
            _LOGGER.warning(f"Valeur non numérique reçue: {new_state.state}")
        except Exception as e:
            _LOGGER.error(f"Erreur critique régulation Titan: {e}")

    # 5. Enregistrement du listener
    entry.async_on_unload(
        async_track_state_change_event(hass, shelly_entity, _async_on_power_change)
    )

    # 6. Chargement des plateformes (Switch et Sensor)
    await hass.config_entries.async_forward_entry_setups(entry, ["switch", "sensor"])

    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Déchargement de l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["switch", "sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
