from homeassistant.components.sensor import (
    SensorEntity, 
    SensorDeviceClass, 
    SensorStateClass
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfPower
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration des capteurs Titan via le Coordinateur."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Récupération des IDs pour les capteurs d'info
    shelly_id = entry.data.get("shelly_entity")
    titan_id = entry.data.get("titan_device_id")
    
    async_add_entities([
        TitanConsigneSensor(coordinator, entry),
        TitanIntegralSensor(coordinator, entry),
        TitanErrorSensor(coordinator, entry),
        TitanInfoSensor(coordinator, entry, "Source Shelly", shelly_id, "mdi:eye-check"),
        TitanInfoSensor(coordinator, entry, "Cible Titan ID", titan_id, "mdi:battery-bluetooth")
    ])

class TitanBaseSensor(CoordinatorEntity, SensorEntity):
    """Classe de base gérant la mise à jour et les infos de l'appareil."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}
        self._entry = entry

class TitanConsigneSensor(TitanBaseSensor):
    """Affiche la dernière consigne envoyée (W)."""
    _attr_translation_key = "consigne_calculee"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calculator"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_consigne"

    @property
    def native_value(self):
        # Récupère la consigne calculée avec P=0.3 et Deadband=20
        return self.coordinator.data.get("consigne")

class TitanIntegralSensor(TitanBaseSensor):
    """Affiche l'erreur accumulée (Composante I)."""
    _attr_translation_key = "valeur_integrale"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:sigma"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_integral"

    @property
    def native_value(self):
        # Affiche l'intégrale bridée à +/- 200 par l'anti-windup
        return self.coordinator.data.get("integral")

class TitanErrorSensor(TitanBaseSensor):
    """Affiche l'erreur actuelle (Consommation - Target)."""
    _attr_translation_key = "erreur_actuelle"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_erreur"

    @property
    def native_value(self):
        return self.coordinator.data.get("erreur")

class TitanInfoSensor(TitanBaseSensor):
    """Capteur statique pour le debug."""
    def __init__(self, coordinator, entry, name, value, icon):
        super().__init__(coordinator, entry)
        self._attr_name = name
        self._attr_native_value = value
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{name.lower().replace(' ', '_')}"



