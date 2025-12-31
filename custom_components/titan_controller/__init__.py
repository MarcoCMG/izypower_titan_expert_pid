import logging
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .coordinator import TitanPIDCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Configuration de l'intégration via l'UI."""
    
    # 1. Récupération des IDs configurés
    shelly_entity = entry.data.get("shelly_entity")
    titan_id = entry.data.get("titan_device_id")
    
    # 2. Instanciation du Coordinateur (Le nouveau cerveau)
    # On lui passe l'ID du Shelly pour qu'il sache quoi surveiller
    coordinator = TitanPIDCoordinator(hass, entry, shelly_entity)
    
    # On ajoute l'ID Titan au coordinateur pour qu'il puisse envoyer les ordres
    coordinator.titan_device_id = titan_id
    coordinator.enabled = True # Par défaut activé

    # 3. Stockage du coordinateur pour accès par les sensors/switches
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # 4. Premier rafraîchissement des données
    await coordinator.async_config_entry_first_refresh()

    # 5. Chargement des plateformes (sensor, switch, etc.)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch"])
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry):
    """Déchargement propre de l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok




