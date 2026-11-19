# SmartThings for Home Assistant

This repository ships the new SmartThings integration for Home Assistant ahead of its release in Home Assistant itself. It replaces the built-in SmartThings integration while installed.

It is temporary. The same code is proposed for Home Assistant in [home-assistant/core#191668](https://github.com/home-assistant/core/pull/191668). When Home Assistant ships it, Home Assistant shows a repair notice asking you to remove this version.

> [!IMPORTANT]
> While this version is installed, Home Assistant does not update the built-in SmartThings integration. Report problems in [this repository's issues](https://github.com/SmartThingsCommunity/ha-smartthings/issues), not to Home Assistant.

Requires Home Assistant 2026.10.0 or newer.

## Install with HACS

1. In HACS, open the menu in the top right and select **Custom repositories**.
2. Add `https://github.com/SmartThingsCommunity/ha-smartthings` with the type **Integration**.
3. Search HACS for **SmartThings**, open it and select **Download**.
4. Restart Home Assistant.

Your existing SmartThings devices and settings stay in place.

## Install manually

1. Download the latest release from the [releases page](https://github.com/SmartThingsCommunity/ha-smartthings/releases).
2. Copy the `custom_components/smartthings` folder into the `custom_components` folder of your Home Assistant configuration directory, the folder that holds `configuration.yaml`. Create `custom_components` if it doesn't exist.
3. Restart Home Assistant.

## Removing this integration

1. In HACS, open **SmartThings**, open the menu and select **Remove**. If you installed manually, delete `custom_components/smartthings`.
2. Restart Home Assistant. The built-in SmartThings integration takes over again.

If you removed this version **before** Home Assistant includes the new integration, SmartThings entries that you added or reauthenticated with this version will fail to load in the built-in integration. Delete those entries and add SmartThings again, which the built-in integration only allows with Home Assistant Cloud.

## Maintainers

`custom_components/smartthings` is generated. Do not edit it by hand.

It is the core code at the commit in [`CORE_REF`](CORE_REF), plus the overlay in [`overlay/`](overlay):

- `manifest.json`: adds `version`, `issue_tracker`, `documentation` and `codeowners`, drops `quality_scale`, and turns the exact `pysmartthings` pin into a range, as hassfest requires for custom integrations.
- `retire.py`, hooked into `async_setup_entry`: shows the repair notice once Home Assistant contains the merged code.
- `translations/en.json`: the text of that repair notice.
- `brand/`: the SmartThings icon and logo, which HACS requires in the repository even though core already has them.

To update from core:

```bash
# In the core checkout, at the commit you want
python3 -m script.translations develop --integration smartthings
git rev-parse HEAD > ../ha-smartthings/CORE_REF

# In this repository
python3 scripts/sync_from_core.py --core ../core
```

Bump `version` in `overlay/manifest.json` for every release. CI fails if the integration doesn't match `CORE_REF` plus the overlay.

## License

Licensed under the [Apache License 2.0](LICENSE.md). The integration is taken from [Home Assistant](https://github.com/home-assistant/core), with the changes listed under [Maintainers](#maintainers).
