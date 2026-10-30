# Dispensa for Home Assistant

![Dispensa icon](https://raw.githubusercontent.com/giuseppe99barchetta/dispensa-home-assistant/main/custom_components/dispensa/brand/icon.png)

Dispensa provides a local, read-only custom integration. It requires neither MQTT nor the Home Assistant token used for outgoing notifications. It polls `/api/home-assistant` every five minutes, so menu changes appear at the next refresh. Dates follow the Dispensa server: configure the same time zone on both servers.

## Install with HACS

The integration requires Home Assistant 2024.5 or later. Your installed version and connection must still be verified on your own system.

1. Update the Dispensa service using your usual procedure. Do not create a second instance of the stack.
2. In HACS, open **⋮ → Custom repositories**, enter `https://github.com/giuseppe99barchetta/dispensa-home-assistant`, select **Integration**, and add it.
3. Find **Dispensa** in HACS and download it. HACS installs only the Home Assistant component; update the Dispensa server separately.
4. Restart Home Assistant. Under **Settings → Devices & services → Add integration**, select **Dispensa** and enter its address reachable from Home Assistant, for example `http://192.168.1.10:9284`. Do not use `localhost` when Dispensa runs in another container or device. A reverse-proxy base path is supported.
5. Open the new Dispensa device and add its entities to your dashboard. Find their actual entity IDs on their respective entity pages.

This is a custom repository, not an entry in the default HACS catalog. Alternatively, copy `custom_components/dispensa` to `<Home Assistant configuration>/custom_components/dispensa`, including all files and subdirectories, and restart Home Assistant.

Like the dashboard, the API has no password: restrict access to a trusted network or protect it at the proxy. Home Assistant must trust the certificate when HTTPS uses a private CA. Images from `entity_picture` are loaded by the browser or Companion App, so the configured address must also be reachable from the viewing device. Browsers may block HTTP images on an HTTPS dashboard.

Home Assistant 2026.3 and later can use the bundled `brand` icon. Some HACS versions still show a placeholder in the integration list because they request icons from a separate brand service. The icon in this page does not change that HACS behavior.

## Entities

- **Today's lunch** and **Today's dinner**: title and picture, with date, status, menu status, inclusion, servings, ingredients, instructions, estimated time and estimated nutrition per serving in the attributes. A selected single meal replaces the planned meal. Draft status is retained; an excluded slot shows “Non previsto”. The statuses `done`, `skipped`, `prepared`, `applying` and `needs-review` retain their meanings in Dispensa.
- **Pantry products**, **expiring lots**, **expired lots**, **lots with unknown expiry** and **products below minimum**: counts from Grocy. Expiring means today through the following three days. Lists of lots and low-stock products are available as attributes. Unknown expiry is never treated as expired. When Grocy is unavailable, affected sensors become unavailable instead of reporting a misleading zero.
- **Available preparations** and **operations to review**: preparations with remaining portions and rows representing pending or interrupted operations. The latter counts rows across Dispensa status categories, not necessarily distinct operations.
- **Items to buy**: count of unchecked entries and the list as an attribute, recalculated for the current menu using current stock. The sensor is unavailable without a current menu or when Grocy is unreachable. Reading it does not change the list.

Meal pictures come from the recipe's selected photo, the existing Dispensa photo cache, or a representative image from the bundled catalog matched to the dish name. Polling does not start a remote image search. Attributes include author, license and source when available. Illustrative images do not certify what the dish looks like.

For example, replace these IDs with the actual ones created on your system:

```yaml
type: vertical-stack
cards:
  - type: picture-entity
    entity: sensor.dispensa_pranzo_di_oggi
    show_state: true
  - type: picture-entity
    entity: sensor.dispensa_cena_di_oggi
    show_state: true
  - type: entities
    entities:
      - sensor.dispensa_lotti_in_scadenza
      - sensor.dispensa_prodotti_sotto_il_minimo
      - sensor.dispensa_articoli_da_acquistare
      - sensor.dispensa_operazioni_da_verificare
```

Attributes are also available in templates and automations. The integration does not approve menus, check off shopping entries or change Grocy. Stock reviews and confirmations remain in Dispensa.

