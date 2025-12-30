import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN, REGULATION_PROFILES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Configuration de l'intégration via l'UI."""
    
    # 1. Récupération des paramètres configurés
    shelly_entity = entry.data.get("shelly_entity")
    static_titan_id = entry.data.get("titan_device_id")
    
    # On vérifie les options d'abord (pour le changement dynamique), sinon les data initiales
    mode_regulation = entry.options.get("mode_regulation", entry.data.get("mode_regulation", "Équilibré"))
    
    # Récupération du profil depuis const.py
    conf = REGULATION_PROFILES.get(mode_regulation)

    # 2. Stockage de l'état interne
    class TitanState:
        def __init__(self):
            self.integral = 0
            self.last_error = 0
            self.history = []
            self.last_consigne = 0
            self.enabled = False  # Activé/Désactivé via le switch

    state = TitanState()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = state

    # 3. CRÉATION DE L'APPAREIL DANS HA
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Régulateur Titan Expert",
        manufacturer="IzyPower",
        model=f"Expert PID ({mode_regulation})",
    )

    # 4. Boucle de régulation PID
    async def _async_on_power_change(event):
        if not state.enabled:
            return

        new_state = event.data.get("new_state")
        if new_state is None or new_state.state in ["unknown", "unavailable", "none"]:
            return

        try:
            puissance_brute = float(new_state.state)
            
            # --- FILTRAGE (Moyenne glissante sur 3 valeurs comme YAML) ---
            state.history.append(puissance_brute)
            if len(state.history) > 3:
                state.history.pop(0)
            
            puissance_filtree = sum(state.history) / len(state.history)
            
            # --- CALCULS PID ---
            # Cible (Target) récupérée du profil (ex: -25W pour Perf)
            erreur = puissance_filtree - conf["target"]
            
            # Calcul du D (Dérivée) : Erreur actuelle - Dernière erreur
            delta_erreur = erreur - state.last_error
            state.last_error = erreur

            # Calcul I (Intégrale) avec Anti-Windup strict du YAML (-400 à 400)
            state.integral = max(-400, min(400, state.integral + erreur))
            
            # Somme PID brute
            p_term = conf["p"] * erreur
            i_term = conf["i"] * state.integral
            d_term = conf["d"] * delta_erreur
            
            correction_brute = p_term + i_term + d_term

            # --- ASYMÉTRIE DYNAMIQUE (Logique YAML) ---
            # Si erreur > 0 (Consommation) -> On utilise max_up (ex: 2500)
            # Si erreur < 0 (Injection) -> On utilise max_down (ex: 400)
            limit = conf["max_up"] if erreur > 0 else conf["max_down"]
            
            # On bride la correction totale par cette limite
            correction_bridee = max(-limit, min(limit, correction_brute))
            
            # --- CALCUL ET BORNAGE DE LA CONSIGNE ---
            nouvelle_consigne = max(-4800, min(4800, int(state.last_consigne + correction_bridee)))

            # --- ENVOI DES ORDRES (Deadband de 12W pour éviter les micro-ordres) ---
            if abs(erreur) > 12:
                state.last_consigne = nouvelle_consigne
                
                if nouvelle_consigne > 0:  # Mode Décharge
                    await hass.services.async_call(
                        "izypower_titan_private", "discharge",
                        {
                            "device_id": static_titan_id, 
                            "power": nouvelle_consigne, 
                            "soc_limit": 10
                        }
                    )
                elif nouvelle_consigne < 0:  # Mode Charge
                    await hass.services.async_call(
                        "izypower_titan_private", "charge",
                        {
                            "device_id": static_titan_id, 
                            "power": abs(nouvelle_consigne), 
                            "soc_limit": 100
                        }
                    )
        
        except Exception as e:
            _LOGGER.error(f"Erreur régulation Titan Expert: {e}")

    # 5. Enregistrement de l'écouteur d'état (Trigger sur le Shelly)
    entry.async_on_unload(
        async_track_state_change_event(hass, shelly_entity, _async_on_power_change)
    )

    # 6. Chargement des plateformes (Switch pour activer/désactiver, Sensor pour debug)
    await hass.config_entries.async_forward_entry_setups(entry, ["switch", "sensor"])
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Déchargement propre de l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["switch", "sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok



