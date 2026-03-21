"""Campaign lifecycle goal server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.campaign.campaign_lifecycle_goal_service import (
    register_campaign_lifecycle_goal_tools,
)

campaign_lifecycle_goal_server = FastMCP[Any]()

register_campaign_lifecycle_goal_tools(campaign_lifecycle_goal_server)
