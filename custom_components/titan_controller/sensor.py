from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration des capteurs Titan."""
    state = hass.data[DOMAIN][entry.entry_id]
    
    # Récupération des IDs de configuration pour le debug
    shelly_id = entry.data.get("shelly_entity")
    titan_id = entry.data.get("titan_device_id")
    
    async_add_entities([
        TitanConsigneSensor(state, entry),
        TitanIntegralSensor(state, entry),
        TitanErrorSensor(state, entry),
        TitanInfoSensor(entry, "Source Shelly", shelly_id, "mdi:eye-check"),
        TitanInfoSensor(entry, "Cible Titan ID", titan_id, "mdi:battery-bluetooth")
    ])

class TitanConsigneSensor(SensorEntity):
    """Affiche la dernière consigne envoyée à la batterie (W)."""
    _attr_has_entity_name = True
    _attr_translation_key = "consigne_calculee"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calculator"
    _attr_object_id = "titan_consigne"

    def __init__(self, state, entry):
        self._state = state
        self._attr_unique_id = f"{entry.entry_id}_consigne"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def native_value(self):
        return self._state.last_consigne

class TitanIntegralSensor(SensorEntity):
    """Affiche la valeur de l'erreur accumulée (Composante I)."""
    _attr_has_entity_name = True
    _attr_translation_key = "valeur_integrale"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:sigma"
    _attr_object_id = "titan_integral"

    def __init__(self, state, entry):
        self._state = state
        self._attr_unique_id = f"{entry.entry_id}_integral"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def native_value(self):
        return round(self._state.integral, 2)

class TitanErrorSensor(SensorEntity):
    """Affiche l'erreur actuelle par rapport à la cible (Terme P)."""
    _attr_has_entity_name = True
    _attr_translation_key = "erreur_actuelle"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:alert-circle-outline"
    _attr_object_id = "titan_erreur"

    def __init__(self, state, entry):
        self._state = state
        self._attr_unique_id = f"{entry.entry_id}_erreur"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def native_value(self):
        return round(self._state.last_error, 2)

class TitanInfoSensor(SensorEntity):
    """Affiche les informations de configuration (Debug)."""
    _attr_has_entity_name = True

    def __init__(self, entry, name, value, icon):
        self._attr_name = name
        self._attr_native_value = value
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{name.lower().replace(' ', '_')}"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}


