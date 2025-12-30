import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

# Importation des constantes
from .const import DOMAIN, MODES_LIST, PROFIL_BALANCED

class TitanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le setup de l'intégration."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=f"Titan PID ({user_input.get('mode_regulation', 'Config')})", 
                data=user_input
            )

        data_schema = vol.Schema({
            vol.Required("shelly_entity"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Required("titan_device_id"): selector.DeviceSelector(
                selector.DeviceSelectorConfig(integration="izypower_titan_private")
            ),
            vol.Required("mode_regulation", default=PROFIL_BALANCED): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=MODES_LIST,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TitanOptionsFlow(config_entry)

class TitanOptionsFlow(config_entries.OptionsFlow):
    """Gère la modification des réglages."""
    
    # On a supprimé le __init__ qui causait l'erreur AttributeError
    
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # On utilise self.config_entry (fourni par la classe parente automatiquement)
        current_mode = self.config_entry.options.get(
            "mode_regulation", 
            self.config_entry.data.get("mode_regulation", PROFIL_BALANCED)
        )

        options_schema = vol.Schema({
            vol.Required("mode_regulation", default=current_mode): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=MODES_LIST,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)


