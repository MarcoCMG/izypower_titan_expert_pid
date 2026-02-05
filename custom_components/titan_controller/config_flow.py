import logging
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

# Importation des constantes
from .const import (
    DOMAIN, MODES_LIST, PROFIL_BALANCED,
    CONF_TITAN_MODE, CONF_TITAN_6K_ID, CONF_TITAN_4K_ID,
    CONF_CAP_6K, CONF_CAP_4K, MODE_SINGLE, MODE_DUAL_AUTO, MODE_DUAL_MANUAL
)

_LOGGER = logging.getLogger(__name__)

class TitanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Gère le setup initial."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Étape initiale utilisateur."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance")

        if user_input is not None:
            # Validation + création
            return self.async_create_entry(
                title=f"Titan PID ({user_input.get('mode_regulation', PROFIL_BALANCED)})",
                data=user_input
            )

        data_schema = vol.Schema({
            vol.Required("shelly_entity"): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="sensor", device_class="power")
            ),
            vol.Required("titan_device_id"): selector.DeviceSelector(
                selector.DeviceSelectorConfig(integration="izypower_titan")
            ),
            vol.Required("mode_regulation", default=PROFIL_BALANCED): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=MODES_LIST,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            # ✅ NOUVEAU : Multi-Titan
            vol.Required("titan_mode", default=MODE_SINGLE): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[MODE_SINGLE, MODE_DUAL_AUTO, MODE_DUAL_MANUAL],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional("titan_6k_id"): str,
            vol.Optional("titan_4k_id"): str,
            vol.Optional("cap_6k", description="kWh"): vol.All(vol.Coerce(float), vol.Range(1, 10)),
            vol.Optional("cap_4k", description="kWh"): vol.All(vol.Coerce(float), vol.Range(1, 10)),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Options flow."""
        return TitanOptionsFlow()

class TitanOptionsFlow(config_entries.OptionsFlow):
    """Gère la modification des réglages."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_mode = self.config_entry.options.get(
            "mode_regulation", 
            self.config_entry.data.get("mode_regulation", PROFIL_BALANCED)
        )
        current_titan_mode = self.config_entry.options.get("titan_mode", MODE_SINGLE)

        options_schema = vol.Schema({
            vol.Required("mode_regulation", default=current_mode): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=MODES_LIST,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            # ✅ Options Multi-Titan
            vol.Required("titan_mode", default=current_titan_mode): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[MODE_SINGLE, MODE_DUAL_AUTO, MODE_DUAL_MANUAL],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Optional("titan_6k_id"): str,
            vol.Optional("titan_4k_id"): str,
            vol.Optional("cap_6k"): vol.All(vol.Coerce(float), vol.Range(1, 10)),
            vol.Optional("cap_4k"): vol.All(vol.Coerce(float), vol.Range(1, 10)),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)




