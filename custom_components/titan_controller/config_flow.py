"""Config Flow Titan Controller."""
import logging
import voluptuous as vol
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, CONF_TITAN_MODE, MODE_SINGLE, MODE_DUAL_AUTO, MODE_DUAL_MANUAL, CONF_TITAN_6K_ID, CONF_TITAN_4K_ID, CONF_MODE_REGULATION, MODES_LIST

_LOGGER = logging.getLogger(__name__)

class TitanControllerConfigFlow(ConfigFlow, domain=DOMAIN):  # ✅ domain=DOMAIN
    VERSION = 1
    
    async def async_step_user(self, user_input=None) -> FlowResult:
        """Étape utilisateur avec formulaire."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance")
        
        # ✅ Schema COMPLET vos choix
        schema = vol.Schema({
            vol.Required(CONF_TITAN_MODE): vol.SelectSelector({
                "options": [MODE_SINGLE, MODE_DUAL_AUTO, MODE_DUAL_MANUAL]
            }),
            vol.Optional(CONF_TITAN_6K_ID): str,
            vol.Optional(CONF_TITAN_4K_ID): str,
            vol.Required(CONF_MODE_REGULATION): vol.SelectSelector({
                "options": MODES_LIST  # Vos profils PID !
            })
        })
        
        if user_input is not None:
            _LOGGER.info(f"Titan config: {user_input}")
            return self.async_create_entry(
                title=f"Titan PID {user_input[CONF_MODE_REGULATION]} ({user_input[CONF_TITAN_MODE]})",
                data=user_input
            )
        
        return self.async_show_form(
            step_id="user",
            data_schema=schema
        )






