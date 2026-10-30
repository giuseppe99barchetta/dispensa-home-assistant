"""Sensors backed by a single shared Dispensa snapshot."""
from urllib.parse import urljoin

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities(DispensaSensor(entry, key) for key in (
        'lunch', 'dinner', 'products', 'expiring', 'expired', 'unknown_expiry', 'low_stock', 'shopping', 'thaw',
        'leftovers', 'unresolved'))


class DispensaSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, entry, key):
        super().__init__(entry.runtime_data)
        self.key = key
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)}, name="Dispensa",
                                            configuration_url=entry.runtime_data.client.url)
        self._attr_icon = {'lunch': 'mdi:food', 'dinner': 'mdi:food-variant', 'products': 'mdi:fridge',
                           'expiring': 'mdi:calendar-alert', 'expired': 'mdi:calendar-remove',
                           'low_stock': 'mdi:cart-arrow-down',
                           'shopping': 'mdi:cart-outline',
                           'thaw': 'mdi:snowflake-melt',
                           'unknown_expiry': 'mdi:calendar-question', 'leftovers': 'mdi:food-takeout-box',
                           'unresolved': 'mdi:alert-circle-outline'}[key]

    @property
    def available(self):
        if not super().available:
            return False
        if self.key in {'products', 'expiring', 'expired', 'unknown_expiry', 'low_stock'}:
            return (self.coordinator.data.get('inventory') or {}).get(self.key) is not None
        if self.key == 'shopping':
            return self.coordinator.data.get('shopping') is not None
        if self.key == 'thaw':
            return self.coordinator.data.get('thaw') is not None
        return True

    @property
    def native_value(self):
        data = self.coordinator.data
        if self.key in ('lunch', 'dinner'):
            item = data['meals'].get(self.key)
            return item['meal']['title'] if item and item['meal'].get('included', True) else 'Non previsto'
        if self.key == 'leftovers':
            return len(data['leftovers'])
        if self.key == 'unresolved':
            return data['unresolved_operations']
        if self.key == 'shopping':
            return sum(not item['checked'] for item in (data.get('shopping') or {}).get('items', []))
        if self.key == 'thaw':
            return len(data.get('thaw') or [])
        value = (data.get('inventory') or {}).get(self.key)
        return len(value) if isinstance(value, list) else value

    @property
    def entity_picture(self):
        if self.key not in ('lunch', 'dinner'):
            return None
        item = self.coordinator.data['meals'].get(self.key)
        if not item or not item['meal'].get('included', True):
            return None
        photo = item['photo']['url']
        return urljoin(self.coordinator.client.url + '/', photo.lstrip('/') if photo.startswith('/') else photo)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        if self.key in ('lunch', 'dinner'):
            item = data['meals'].get(self.key)
            if not item:
                return {'data': data['date']}
            meal = item['meal']
            photo = item['photo']
            return {'data': data['date'], 'stato': item['status'], 'stato_menu': item['plan_status'],
                    'incluso': meal.get('included', True), 'porzioni': meal.get('servings'),
                    'ingredienti': meal.get('ingredients', []), 'istruzioni': meal.get('instructions'),
                    'minuti_stimati': meal.get('estimated_minutes'), 'nutrizione_per_porzione': meal.get('nutrition'),
                    'foto_autore': photo.get('author'), 'foto_licenza': photo.get('license'),
                    'foto_fonte': photo.get('source_url')}
        if self.key in ('expiring', 'expired', 'low_stock'):
            return {'prodotti': (data.get('inventory') or {}).get(self.key, [])}
        if self.key == 'leftovers':
            return {'preparazioni': data['leftovers']}
        if self.key == 'shopping':
            result = data.get('shopping') or {}
            return {'prodotti': result.get('items', []), 'stato_menu': result.get('plan_status')}
        if self.key == 'thaw':
            return {'prodotti': data.get('thaw') or []}
        return {}

