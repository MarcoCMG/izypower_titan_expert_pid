import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN
from .coordinator import TitanPIDCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Configuration de l'intégration via l'UI."""
    
    # 1. Récupération des IDs
    shelly_entity = entry.data.get("shelly_entity")
    titan_id = entry.data.get("titan_device_id")
    
    # 2. Instanciation du Coordinateur
    coordinator = TitanPIDCoordinator(hass, entry, shelly_entity)
    coordinator.titan_device_id = titan_id
    coordinator.enabled = True 

    # --- AJOUT : IDENTIFICATION DE L'APPAREIL (Évite le "undefined") ---
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="Titan : Régulation Expert PID",
        manufacturer="IzyPower",
        model="Expert PID Controller",
    )

    # 3. Stockage pour accès par les sensors/switches
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # 4. Premier rafraîchissement des données
    await coordinator.async_config_entry_first_refresh()

    # --- ÉLÉMENT CRUCIAL : ÉCOUTEUR DE MISE À JOUR ---
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # 5. Chargement des plateformes
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch"])
    
    return True

async def update_listener(hass: HomeAssistant, entry):
    """Force le rechargement de l'intégration quand tu modifies les options."""
    _LOGGER.info("Profil Titan modifié. Rechargement de l'intégration.")
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry):
    """Déchargement propre de l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


# ✅ AJOUT : Services privés PID
from .services import async_setup_services
await async_setup_services(hass)

return True






