from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration des interrupteurs Titan."""
    state = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TitanControlSwitch(state, entry)])

class TitanControlSwitch(SwitchEntity):
    """Interrupteur pour activer/désactiver la régulation PI."""

    # Utilisation des clés de traduction pour le nom (défini dans fr.json)
    _attr_has_entity_name = True
    _attr_translation_key = "reg_switch"
    _attr_icon = "mdi:rocket-launch"

    def __init__(self, state, entry):
        """Initialisation de l'interrupteur."""
        self._state = state
        self._entry = entry
        # L'ID unique permet de garder l'entité liée même si on change son nom
        self._attr_unique_id = f"{entry.entry_id}_reg_switch"
        # On définit le device_info pour que le switch soit rattaché à l'appareil Titan
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }

    @property
    def is_on(self):
        """Retourne l'état actuel de la régulation (activé/désactivé)."""
        return self._state.enabled

    async def async_turn_on(self, **kwargs):
        """Active la régulation."""
        self._state.enabled = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Désactive la régulation et envoie l'ordre d'arrêt immédiat."""
        self._state.enabled = False
        
        # Récupération du device_id du Titan
        titan_id = self._entry.data.get("titan_device_id")
        
        # Appel du service de stop
        await self.hass.services.async_call(
            "izypower_titan_private", 
            "stop",
            {"device_id": titan_id}
        )
        
        # Réinitialisation des variables de calcul pour éviter un "bond" à la reprise
        self._state.last_consigne = 0
        self._state.integral = 0
        
        self.async_write_ha_state()
