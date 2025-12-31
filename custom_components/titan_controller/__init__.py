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
    
    # 2. Instanciation du Coordinateur
    coordinator = TitanPIDCoordinator(hass, entry, shelly_entity)
    coordinator.titan_device_id = titan_id
    coordinator.enabled = True 

    # 3. Stockage du coordinateur
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # 4. Premier rafraîchissement
    await coordinator.async_config_entry_first_refresh()

    # --- AJOUT SÉCURITÉ : ÉCOUTE DES CHANGEMENTS D'OPTIONS ---
    # Cette ligne lie ton OptionsFlow au rechargement de l'intégration
    entry.async_on_unload(entry.add_update_listener(update_listener))

    # 5. Chargement des plateformes
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor", "switch"])
    
    return True

async def update_listener(hass: HomeAssistant, entry):
    """Relance l'intégration dès qu'on change un mode dans les options."""
    _LOGGER.info("Profil de régulation Titan modifié, rechargement...")
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry):
    """Déchargement propre."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor", "switch"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok





