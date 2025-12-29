import logging
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers import device_registry as dr, entity_registry as er
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Configuration de l'intégration via l'UI."""
    
    # 1. Récupération des paramètres configurés
    shelly_entity = entry.data.get("shelly_entity")
    static_titan_id = entry.data.get("titan_device_id")
    p_factor = entry.data.get("facteur_p", 0.7)
    i_factor = entry.data.get("facteur_i", 0.2)

    # 2. Stockage de l'état interne (DÉSACTIVÉ PAR DÉFAUT)
    class TitanState:
        def __init__(self):
            self.integral = 0
            self.history = []
            self.last_consigne = 0
            self.enabled = False  # <--- Sécurité : Désactivé à l'installation

    state = TitanState()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = state

    # 3. CRÉATION DE L'APPAREIL DU RÉGULATEUR
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
        # Si le switch est sur OFF, on ne fait strictement rien
        if not state.enabled:
            return

        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ["unknown", "unavailable", "none"]:
            return

        try:
            puissance_brute = float(new_state.state)
            
            # --- LOGIQUE DYNAMIQUE DE L'ID (Comme en YAML) ---
            ent_reg = er.async_get(hass)
            sn_entity_id = "sensor.izypower_titan_192_168_68_59_titan_device_sn"
            entry_sn = ent_reg.async_get(sn_entity_id)
            
            if entry_sn and entry_sn.device_id:
                active_titan_id = entry_sn.device_id
            else:
                active_titan_id = static_titan_id
            # ------------------------------------------------

            # Filtrage & Calculs
            state.history.append(puissance_brute)
            if len(state.history) > 2:
                state.history.pop(0)
            
            puissance_filtree = sum(state.history) / len(state.history)
            erreur = puissance_filtree - 0 
            state.integral = max(-500, min(500, state.integral + erreur))
            
            correction_brute = (p_factor * erreur) + (i_factor * state.integral)
            max_step = 2500 if erreur < 0 else 600
            correction_bridee = max(-max_step, min(max_step, correction_brute))
            
            # Nouvelle consigne (bridage 4800W)
            nouvelle_consigne = max(-4800, min(4800, int(state.last_consigne + correction_bridee)))
            state.last_consigne = nouvelle_consigne

            if abs(puissance_filtree) > 8:
                if nouvelle_consigne > 0:
                    await hass.services.async_call(
                        "izypower_titan_private", "discharge",
                        {
                            "device_id": active_titan_id,
                            "power": nouvelle_consigne, 
                            "soc_limit": 10
                        }
                    )
                elif nouvelle_consigne < 0:
                    await hass.services.async_call(
                        "izypower_titan_private", "charge",
                        {
                            "device_id": active_titan_id,
                            "power": abs(nouvelle_consigne), 
                            "soc_limit": 100
                        }
                    )
        
        except ValueError:
            _LOGGER.warning(f"Valeur Shelly non numérique : {new_state.state}")
        except Exception as e:
            _LOGGER.error(f"Erreur régulation Titan : {e}")

    # 5. Enregistrement du listener
    entry.async_on_unload(
        async_track_state_change_event(hass, shelly_entity, _async_on_power_change)
    )

    # 6. Chargement des plateformes
    await hass.config_entries.async_forward_entry_setups(entry, ["switch", "sensor"])
    
    _LOGGER.info("Régulateur Titan Expert chargé (en attente d'activation manuelle).")
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["switch", "sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
