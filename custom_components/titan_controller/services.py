"""Proxy services vers khirale/izypower_titan."""

import logging
import asyncio
from homeassistant.core import HomeAssistant, ServiceCall
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_services(hass: HomeAssistant) -> None:
    """Setup proxy services."""
    
    config = hass.data[DOMAIN]
    
    async def proxy_forward(service_name: str):
        async def handler(call: ServiceCall) -> None:
            # Forward vers khirale
            titan_config = config["titan_config"]
            
            if titan_config["mode"] == "single":
                await hass.services.async_call(
                    "izypower_titan", service_name, call.data)
            else:  # dual
                ratios = titan_config["ratios"]
                p1 = call.data["power"] * (ratios["ratio_6k"] / 100)
                p2 = call.data["power"] * (ratios["ratio_4k"] / 100)
                
                tasks = [
                    hass.services.async_call("izypower_titan", service_name, {
                        "device_id": titan_config["titan_6k_id"],
                        "power": int(p1), "soc_limit": call.data["soc_limit"]
                    }),
                    hass.services.async_call("izypower_titan", service_name, {
                        "device_id": titan_config["titan_4k_id"], 
                        "power": int(p2), "soc_limit": call.data["soc_limit"]
                    })
                ]
                await asyncio.gather(*tasks)
            
            _LOGGER.debug(f"{service_name}_private → {call.data}")
        
        return handler
    
    # 3 proxies
    hass.services.async_register(DOMAIN, "discharge_private", 
                                proxy_forward("discharge"))
    hass.services.async_register(DOMAIN, "charge_private", 
                                proxy_forward("charge"))
    hass.services.async_register(DOMAIN, "stop_private", 
                                proxy_forward("stop"))

