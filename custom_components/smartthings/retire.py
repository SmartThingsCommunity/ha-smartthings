"""Tell users to remove this custom integration once core ships the same code."""

import logging
from pathlib import Path

import homeassistant.components
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

ISSUE_ID = "custom_version_superseded"
LEARN_MORE_URL = (
    "https://github.com/SmartThingsCommunity/ha-smartthings#removing-this-integration"
)
# A file the core PR adds. Its presence in core means the merged code shipped.
CORE_MARKER = Path("smartthings", "app_ledger.py")


def _core_has_merged_code() -> bool:
    """Return if the core smartthings integration contains the merged code."""
    return (
        Path(homeassistant.components.__file__).parent.joinpath(CORE_MARKER).is_file()
    )


async def async_check_core_merged(hass: HomeAssistant) -> None:
    """Show a repair issue when core supersedes this custom integration.

    Never raises: a failed check must not affect setup.
    """
    try:
        merged = await hass.async_add_executor_job(_core_has_merged_code)
        if merged:
            ir.async_create_issue(
                hass,
                DOMAIN,
                ISSUE_ID,
                is_fixable=False,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_ID,
                learn_more_url=LEARN_MORE_URL,
            )
        else:
            ir.async_delete_issue(hass, DOMAIN, ISSUE_ID)
    except Exception:
        _LOGGER.debug("Could not check the core smartthings integration", exc_info=True)
