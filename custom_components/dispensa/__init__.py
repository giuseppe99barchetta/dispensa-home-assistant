"""Home Assistant integration for Dispensa."""
from datetime import timedelta
import logging

import voluptuous as vol

from homeassistant.const import CONF_URL, Platform
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import DispensaClient, DispensaError
from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]
MEALS = ("lunch", "dinner")
MARK_SCHEMA = vol.Schema({
    vol.Required("meal"): vol.In(MEALS),
    vol.Optional("eaten", default=True): cv.boolean,
    vol.Optional("date"): cv.date,
})
RATE_SCHEMA = vol.Schema({
    vol.Required("meal"): vol.In(MEALS),
    vol.Required("rating"): vol.All(vol.Coerce(int), vol.Range(min=1, max=5)),
    vol.Optional("tags"): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("note"): cv.string,
    vol.Optional("date"): cv.date,
})


async def _record(hass, call, **extra):
    """Send one outcome to Dispensa, then refresh the sensors. Meal outcome only: never Grocy stock."""
    entries = [e for e in hass.config_entries.async_entries(DOMAIN) if getattr(e, "runtime_data", None)]
    if not entries:
        raise HomeAssistantError("Dispensa non è configurato o non è ancora pronto")
    coordinator = entries[0].runtime_data
    # Default to the Dispensa server's own "today", as dates follow that server.
    day = call.data.get("date")
    day = day.isoformat() if day else (coordinator.data or {}).get("date")
    if not day:
        raise HomeAssistantError("Data di oggi non disponibile da Dispensa: indica la data")
    try:
        await coordinator.client.set_eaten(day, call.data["meal"], **extra)
    except DispensaError as exc:
        raise HomeAssistantError(f"Dispensa: {exc}") from exc
    await coordinator.async_request_refresh()


def _register_services(hass):
    async def mark_eaten(call):
        await _record(hass, call, eaten=call.data["eaten"])

    async def rate_meal(call):
        await _record(hass, call, eaten=True, rating=call.data["rating"], tags=call.data.get("tags"),
                      note=call.data.get("note"))

    hass.services.async_register(DOMAIN, "mark_eaten", mark_eaten, schema=MARK_SCHEMA)
    hass.services.async_register(DOMAIN, "rate_meal", rate_meal, schema=RATE_SCHEMA)


class DispensaCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client):
        super().__init__(hass, logger=logging.getLogger(__name__), name=DOMAIN,
                         update_interval=timedelta(minutes=5))
        self.client = client

    async def _async_update_data(self):
        try:
            return await self.client.snapshot()
        except DispensaError as exc:
            raise UpdateFailed(str(exc)) from exc


async def async_setup_entry(hass, entry):
    coordinator = DispensaCoordinator(hass, DispensaClient(async_get_clientsession(hass), entry.data[CONF_URL]))
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    if not hass.services.has_service(DOMAIN, "mark_eaten"):
        _register_services(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded and not [e for e in hass.config_entries.async_entries(DOMAIN) if e is not entry]:
        for name in ("mark_eaten", "rate_meal"):
            hass.services.async_remove(DOMAIN, name)
    return unloaded
