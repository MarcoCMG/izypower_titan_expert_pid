from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration de l'interrupteur de pilotage Titan."""
    # On récupère l'état interne créé dans le __init__.py
    state = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TitanControlSwitch(state, entry)])

class TitanControlSwitch(SwitchEntity):
    """Interrupteur pour activer/désactiver la régulation PI."""

    # Paramètres d'affichage
    _attr_has_entity_name = True
    _attr_translation_key = "reg_switch" # Doit être défini dans ton fr.json
    _attr_icon = "mdi:rocket-launch"

    def __init__(self, state, entry):
        """Initialisation de l'interrupteur."""
        self._state = state
        self._entry = entry
        # ID unique basé sur l'entrée de configuration
        self._attr_unique_id = f"{entry.entry_id}_reg_switch"
        
        # Rattachement automatique à l'appareil "Régulateur Titan Expert"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    @property
    def is_on(self):
        """
        Retourne l'état actuel. 
        Sera à 'False' (OFF) par défaut à l'installation car 
        state.enabled est initialisé à False dans __init__.py.
        """
        return self._state.enabled

    async def async_turn_on(self, **kwargs):
        """Active la régulation."""
        self._state.enabled = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Désactive la régulation et sécurise la batterie."""
        self._state.enabled = False
        
        # --- RECHERCHE DYNAMIQUE DE L'ID (Identique à ton YAML) ---
        # Cela évite que le service 'stop' échoue si l'ID a changé
        ent_reg = er.async_get(self.hass)
        sn_entity_id = "sensor.izypower_titan_192_168_68_59_titan_device_sn"
        entry_sn = ent_reg.async_get(sn_entity_id)
        
        if entry_sn and entry_sn.device_id:
            active_titan_id = entry_sn.device_id
        else:
            # Fallback sur l'ID stocké lors de la configuration initiale
            active_titan_id = self._entry.data.get("titan_device_id")
        
        # 1. Envoi de l'ordre d'arrêt immédiat à la batterie
        await self.hass.services.async_call(
            "izypower_titan_private", 
            "stop",
            {"device_id": active_titan_id}
        )
        
        # 2. RÉINITIALISATION DES VARIABLES (Anti-bond)
        # On remet tout à zéro pour que le PID reparte proprement au prochain ON
        self._state.last_consigne = 0
        self._state.integral = 0
        self._state.history = []
        
        self.async_write_ha_state()

