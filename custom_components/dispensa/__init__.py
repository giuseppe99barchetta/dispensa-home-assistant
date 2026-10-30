"""Home Assistant integration for Dispensa."""
from datetime import timedelta
import logging

from homeassistant.const import CONF_URL, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import DispensaClient, DispensaError
from .const import DOMAIN

PLATFORMS = [Platform.SENSOR]


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
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass, entry):
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
