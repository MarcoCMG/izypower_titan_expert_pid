from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration de l'interrupteur de pilotage Titan via le coordinateur."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TitanControlSwitch(coordinator, entry)])

class TitanControlSwitch(CoordinatorEntity, SwitchEntity):
    """Interrupteur pour activer/désactiver la régulation PID Expert."""

    _attr_has_entity_name = True
    _attr_translation_key = "reg_switch"
    _attr_icon = "mdi:rocket-launch"
    _attr_object_id = "titan_auto_pilot"

    def __init__(self, coordinator, entry):
        """Initialisation de l'interrupteur lié au coordinateur."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_reg_switch"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def is_on(self):
        """Retourne l'état d'activation stocké dans le coordinateur."""
        return self.coordinator.enabled

    async def async_turn_on(self, **kwargs):
        """Active la régulation."""
        self.coordinator.enabled = True
        # Force une mise à jour immédiate pour relancer le calcul
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Désactive la régulation, arrête la batterie et reset le PID."""
        self.coordinator.enabled = False
        
        # 1. Ordre d'arrêt immédiat à la batterie Titan
        active_titan_id = self.coordinator.titan_device_id
        if active_titan_id:
            try:
                await self.hass.services.async_call(
                    "izypower_titan_private", 
                    "stop",
                    {"device_id": active_titan_id}
                )
            except Exception as e:
                self.coordinator.logger.error("Erreur stop Titan: %s", e)
        
        # 2. RÉINITIALISATION COMPLÈTE DU PID (Nettoyage de la mémoire)
        # On remet à zéro pour éviter un bond de puissance au redémarrage
        self.coordinator.last_consigne = 0
        self.coordinator.integral = 0
        self.coordinator.last_error = 0
        self.coordinator.history.clear() # Vide la deque de la moyenne glissante
        
        self.async_write_ha_state()






