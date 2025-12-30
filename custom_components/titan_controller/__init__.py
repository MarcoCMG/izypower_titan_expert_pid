import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN, REGULATION_PROFILES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Configuration de l'intégration via l'UI."""
    
    # 1. Récupération des paramètres configurés (Dynamique pour chaque utilisateur)
    shelly_entity = entry.data.get("shelly_entity")
    static_titan_id = entry.data.get("titan_device_id")
    mode_regulation = entry.data.get("mode_regulation", "Équilibré")
    
    # Récupération du profil expert depuis const.py
    conf = REGULATION_PROFILES.get(mode_regulation)

    # 2. Stockage de l'état interne
    class TitanState:
        def __init__(self):
            self.integral = 0
            self.last_error = 0
            self.history = []
            self.last_consigne = 0
            self.enabled = False  # Sécurité : Désactivé à l'installation

    state = TitanState()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = state

    # 3. CRÉATION DE L'APPAREIL
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Régulateur Titan Expert",
        manufacturer="IzyPower",
        model=f"Expert PID v1 ({mode_regulation})",
    )

    # 4. Boucle de régulation PID Expert
    # NOTE : On retire @callback car la fonction est async (contient des await)
    async def _async_on_power_change(event):
        if not state.enabled:
            return

        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ["unknown", "unavailable", "none"]:
            return

        try:
            puissance_brute = float(new_state.state)
            
            # --- LOGIQUE UNIVERSELLE ---
            # On utilise l'ID de l'appareil sélectionné par l'utilisateur lors de la config
            active_titan_id = static_titan_id

            # --- FILTRAGE & CALCULS PID ---
            state.history.append(puissance_brute)
            if len(state.history) > 3:
                state.history.pop(0)
            
            puissance_filtree = sum(state.history) / len(state.history)
            
            # Utilisation des paramètres du profil
            erreur = puissance_filtree - conf["target"]
            
            # Calcul du D (Le Frein)
            delta_erreur = erreur - state.last_error
            state.last_error = erreur

            # Calcul I avec Anti-Windup
            if not (state.last_consigne >= 4750 and erreur > 0):
                state.integral = max(-500, min(500, state.integral + erreur))
            
            # Somme PID
            p_term = conf["p"] * erreur
            i_term = conf["i"] * state.integral
            d_term = conf["d"] * delta_erreur
            
            correction_brute = p_term + i_term + d_term

            # --- ASYMÉTRIE ---
            if correction_brute > 0:
                correction_bridee = min(correction_brute, conf["max_up"])
            else:
                correction_bridee = max(correction_brute, -conf["max_down"])
            
            # Nouvelle consigne
            nouvelle_consigne = max(-4800, min(4800, int(state.last_consigne + correction_bridee)))
            state.last_consigne = nouvelle_consigne

            # Envoi des ordres (Zone morte de 10W)
            if abs(erreur) > 10:
                if nouvelle_consigne > 0:
                    await hass.services.async_call(
                        "izypower_titan_private", "discharge",
                        {"device_id": active_titan_id, "power": nouvelle_consigne, "soc_limit": 10}
                    )
                elif nouvelle_consigne < 0:
                    await hass.services.async_call(
                        "izypower_titan_private", "charge",
                        {"device_id": active_titan_id, "power": abs(nouvelle_consigne), "soc_limit": 100}
                    )
        
        except Exception as e:
            _LOGGER.error(f"Erreur régulation Titan Expert: {e}")

    # 5. Enregistrement du listener
    entry.async_on_unload(
        async_track_state_change_event(hass, shelly_entity, _async_on_power_change)
    )

    # 6. Chargement des plateformes
    await hass.config_entries.async_forward_entry_setups(entry, ["switch", "sensor"])
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Déchargement de l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["switch", "sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


