from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers import entity_registry as er
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration de l'interrupteur de pilotage Titan."""
    state = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TitanControlSwitch(state, entry)])

class TitanControlSwitch(SwitchEntity):
    """Interrupteur pour activer/désactiver la régulation PID Expert."""

    _attr_has_entity_name = True
    _attr_translation_key = "pilotage" # Correspond à la clé dans fr.json
    _attr_icon = "mdi:rocket-launch"
    
    # FORCE L'ID TECHNIQUE PRO : switch.titan_pilotage
    _attr_object_id = "titan_pilotage"

    def __init__(self, state, entry):
        """Initialisation de l'interrupteur."""
        self._state = state
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_reg_switch"
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Titan : Régulation Expert PID", # Nom de l'appareil
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
        """Désactive la régulation et sécurise la batterie."""
        self._state.enabled = False
        
        # Recherche dynamique de l'ID pour le service stop
        ent_reg = er.async_get(self.hass)
        sn_entity_id = "sensor.izypower_titan_192_168_68_59_titan_device_sn"
        entry_sn = ent_reg.async_get(sn_entity_id)
        
        active_titan_id = entry_sn.device_id if entry_sn and entry_sn.device_id else self._entry.data.get("titan_device_id")
        
        # 1. Ordre d'arrêt immédiat (Sécurité)
        await self.hass.services.async_call(
            "izypower_titan_private", 
            "stop",
            {"device_id": active_titan_id}
        )
        
        # 2. RÉINITIALISATION COMPLÈTE (Version 30/12)
        # On nettoie tout pour éviter les effets de mémoire au redémarrage
        self._state.last_consigne = 0
        self._state.integral = 0
        self._state.last_error = 0  # Crucial pour le terme Dérivé (D)
        self._state.history = []
        
        self.async_write_ha_state()



