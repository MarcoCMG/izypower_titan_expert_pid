from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration des interrupteurs Titan."""
    state = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TitanControlSwitch(state, entry)])

class TitanControlSwitch(SwitchEntity):
    """Interrupteur pour activer/désactiver la régulation PI."""

    def __init__(self, state, entry):
        self._state = state
        self._entry = entry
        self._attr_name = "Pilotage Titan Auto"
        self._attr_unique_id = f"{entry.entry_id}_reg_switch"
        self._attr_icon = "mdi:rocket-launch"

    @property
    def is_on(self):
        """Retourne l'état de l'interrupteur."""
        return self._state.enabled

    async def async_turn_on(self, **kwargs):
        """Active la régulation."""
        self._state.enabled = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Désactive la régulation et arrête le Titan."""
        self._state.enabled = False
        # On appelle le service stop comme dans votre YAML
        titan_id = self._entry.data.get("titan_device_id")
        await self.hass.services.async_call(
            "izypower_titan_private", "stop",
            {"device_id": titan_id}
        )
        # On remet la consigne à zéro en interne
        self._state.last_consigne = 0
        self._state.integral = 0
        self.async_write_ha_state()