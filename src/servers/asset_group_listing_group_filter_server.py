"""Asset group listing group filter server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.assets.asset_group_listing_group_filter_service import (
    register_asset_group_listing_group_filter_tools,
)

asset_group_listing_group_filter_server = FastMCP[Any]()

register_asset_group_listing_group_filter_tools(asset_group_listing_group_filter_server)
