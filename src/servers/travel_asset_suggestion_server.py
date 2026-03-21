"""Travel asset suggestion server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.assets.travel_asset_suggestion_service import (
    register_travel_asset_suggestion_tools,
)

travel_asset_suggestion_server = FastMCP[Any]()

register_travel_asset_suggestion_tools(travel_asset_suggestion_server)
