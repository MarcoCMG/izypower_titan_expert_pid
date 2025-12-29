from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPower
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Configuration des capteurs Titan."""
    state = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        TitanConsigneSensor(state, entry),
        TitanIntegralSensor(state, entry)
    ])

class TitanConsigneSensor(SensorEntity):
    """Affiche la dernière consigne calculée."""
    _attr_has_entity_name = True
    _attr_translation_key = "consigne_calculee"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calculator"

    def __init__(self, state, entry):
        self._state = state
        self._attr_unique_id = f"{entry.entry_id}_consigne"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def native_value(self):
        return self._state.last_consigne

class TitanIntegralSensor(SensorEntity):
    """Affiche la valeur de l'accumulateur intégral (I)."""
    _attr_has_entity_name = True
    _attr_translation_key = "valeur_integrale"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:sigma"

    def __init__(self, state, entry):
        self._state = state
        self._attr_unique_id = f"{entry.entry_id}_integral"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    @property
    def native_value(self):
        return round(self._state.integral, 2)
