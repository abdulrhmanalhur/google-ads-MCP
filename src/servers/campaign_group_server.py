"""Campaign group server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.campaign.campaign_group_service import register_campaign_group_tools

campaign_group_server = FastMCP[Any]()

register_campaign_group_tools(campaign_group_server)
