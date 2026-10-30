"""Configure a Dispensa server from the Home Assistant UI."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_URL
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .client import DispensaClient, DispensaError, normalize_url
from .const import DOMAIN


class DispensaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            try:
                url = normalize_url(user_input[CONF_URL])
                await DispensaClient(async_get_clientsession(self.hass), url).snapshot()
            except ValueError:
                errors['base'] = 'invalid_url'
            except DispensaError:
                errors['base'] = 'cannot_connect'
            else:
                await self.async_set_unique_id(url)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title="Dispensa", data={CONF_URL: url})
        return self.async_show_form(step_id="user", data_schema=vol.Schema({vol.Required(CONF_URL): str}),
                                    errors=errors)
