import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

DOMAIN = "titan_controller"

class TitanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le setup de l'intégration via l'interface."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="Régulateur Titan", data=user_input)

        # Formulaire de configuration
        data_schema = vol.Schema({
            vol.Required("shelly_entity"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Required("titan_device_id"): selector.DeviceSelector(
                selector.DeviceSelectorConfig(integration="izypower_titan_private")
            ),
            vol.Optional("facteur_p", default=0.7): vol.Coerce(float),
            vol.Optional("facteur_i", default=0.2): vol.Coerce(float),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)