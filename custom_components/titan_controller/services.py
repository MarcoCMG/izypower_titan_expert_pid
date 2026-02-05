"""Services privés IzyPower Titan pour PID."""

import logging
from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_services(hass: HomeAssistant) -> None:
    """Setup private services."""
    
    async def titan_discharge_private(service: ServiceCall) -> None:
        device_id = service.data["device_id"]
        power = int(service.data["power"])
        soc_limit = int(service.data["soc_limit"])
        
        # Appelle ta logique RPC existante
        await hass.services.async_call(
            DOMAIN, "discharge",
            {"device_id": device_id, "power": power, "soc_limit": soc_limit}
        )
        _LOGGER.debug(f"Titan {device_id} discharge_private: {power}W, SOC:{soc_limit}%")
    
    async def titan_charge_private(service: ServiceCall) -> None:
        device_id = service.data["device_id"]
        power = int(service.data["power"])
        soc_limit = int(service.data["soc_limit"])
        
        await hass.services.async_call(
            DOMAIN, "charge",
            {"device_id": device_id, "power": power, "soc_limit": soc_limit}
        )
    
    async def titan_stop_private(service: ServiceCall) -> None:
        device_id = service.data["device_id"]
        await hass.services.async_call(
            DOMAIN, "stop", {"device_id": device_id}
        )
    
    # Enregistre les services
    hass.services.async_register(DOMAIN, "discharge_private", titan_discharge_private)
    hass.services.async_register(DOMAIN, "charge_private", titan_charge_private)
    hass.services.async_register(DOMAIN, "stop_private", titan_stop_private)
