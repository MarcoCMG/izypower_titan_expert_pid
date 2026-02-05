"""IzyPower Titan Expert PID."""

import logging
import asyncio
import voluptuous as vol
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er
from .const import (
    DOMAIN, MODES_LIST, REGULATION_PROFILES,
    SENSOR_TITAN_COUNT, SENSOR_TITAN_IDS, SENSOR_TITAN_RATIO,
    SENSOR_TITAN_STATUS, SENSOR_TITAN_TOTAL_CAP, SWITCH_PID_MASTER,
    ICON_TITAN_COUNT, ICON_TITAN_IDS, ICON_TITAN_RATIO,
    ICON_TITAN_STATUS, ICON_TITAN_CAP
)
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "switch"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup intégration."""
    hass.data.setdefault(DOMAIN, {})
    
    # AUTO-DÉTECTION Titans + Config Flow data
    titan_config = await autodetect_titans(hass, entry.data)
    hass.data[DOMAIN]["titan_config"] = titan_config
    hass.data[DOMAIN]["profiles"] = REGULATION_PROFILES
    
    # Services proxy khirale
    await async_setup_services(hass)
    
    # Plateformes
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def autodetect_titans(hass, entry_data):
    """Scan khirale entities → Fusion config flow + auto."""
    titans = {}
    
    # 1. Scan khirale sensors.titan_*
    for state in hass.states.async_all():
        if "_capacity" in state.entity_id and "titan_" in state.entity_id:
           ## ❌ **__init__.py INCOMPLET** → **VERSION COMPLÈTE**

**Problèmes détectés** :
- `autodetect_titans`, `create_status_sensors` → définies mais **pas appelées**
- Classes `TitanPidSwitch`, `PidSensor` → **vides**
- Pas de `async_unload_entry`
- Manque intégration `config_flow`

## ✅ **`__init__.py` FINAL COMPLÈT**
```python
"""IzyPower Titan Expert PID."""

import logging
import asyncio
import voluptuous as vol
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers import entity_registry as er
from .const import (
    DOMAIN, ENTITY_SWITCH_PID, SENSOR_TITAN_COUNT, SENSOR_TITAN_IDS,
    SENSOR_TITAN_RATIO, SENSOR_TITAN_STATUS, SENSOR_TITAN_TOTAL_CAP
)
from .services
