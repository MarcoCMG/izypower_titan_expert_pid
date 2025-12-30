import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

# On importe les constantes depuis ton fichier const.py
from .const import DOMAIN, MODES_LIST 

class TitanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le setup de l'intégration via l'interface avec Profils Expert."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            # Le titre inclura le mode choisi pour plus de clarté
            return self.async_create_entry(
                title=f"Titan PID ({user_input['mode_regulation']})", 
                data=user_input
            )

        # Formulaire de configuration simplifié et expert
        data_schema = vol.Schema({
            vol.Required("shelly_entity"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Required("titan_device_id"): selector.DeviceSelector(
                selector.DeviceSelectorConfig(integration="izypower_titan_private")
            ),
            # Remplacement de P et I par le sélecteur de Profil (Version 30/12)
            vol.Required("mode_regulation", default="Équilibré"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=MODES_LIST,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="mode_regulation" # Lien avec strings.json
                )
            ),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)
