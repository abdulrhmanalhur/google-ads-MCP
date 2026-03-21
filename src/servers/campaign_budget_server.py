"""Campaign budget server module (list and remove operations)."""

from typing import Any

from fastmcp import FastMCP

from src.services.bidding.campaign_budget_service import (
    register_campaign_budget_tools,
)

campaign_budget_server = FastMCP[Any]()

register_campaign_budget_tools(campaign_budget_server)
