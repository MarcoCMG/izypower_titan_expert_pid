from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration de l'interrupteur de pilotage Titan."""
    state = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TitanControlSwitch(state, entry)])

class TitanControlSwitch(SwitchEntity):
    """Interrupteur pour activer/désactiver la régulation PID Expert."""

    _attr_has_entity_name = True
    _attr_translation_key = "reg_switch"
    _attr_icon = "mdi:rocket-launch"
    
    # Force l'ID technique à être court : switch.titan_auto_pilot
    _attr_object_id = "titan_auto_pilot"

    def __init__(self, state, entry):
        """Initialisation de l'interrupteur."""
        self._state = state
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_reg_switch"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Titan : Régulation Expert PID",
        }

    @property
    def is_on(self):
        """Retourne l'état d'activation de la boucle PID."""
        return self._state.enabled

    async def async_turn_on(self, **kwargs):
        """Active la régulation."""
        self._state.enabled = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Désactive la régulation et sécurise la batterie de manière universelle."""
        self._state.enabled = False
        
        # RÉCUPÉRATION DYNAMIQUE (Plus d'IP en dur, on utilise l'ID de la config)
        active_titan_id = self._entry.data.get("titan_device_id")
        
        if active_titan_id:
            # Ordre d'arrêt immédiat (Sécurité)
            await self.hass.services.async_call(
                "izypower_titan_private", 
                "stop",
                {"device_id": active_titan_id}
            )
        
        # RÉINITIALISATION COMPLÈTE DU PID
        self._state.last_consigne = 0
        self._state.integral = 0
        self._state.last_error = 0
        self._state.history = []
        
        self.async_write_ha_state()





