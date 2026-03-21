"""Smart campaign setting server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.campaign.smart_campaign_setting_service import (
    register_smart_campaign_setting_tools,
)

smart_campaign_setting_server = FastMCP[Any]()

register_smart_campaign_setting_tools(smart_campaign_setting_server)
