"""Asset set asset server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.assets.asset_set_asset_service import register_asset_set_asset_tools

asset_set_asset_server = FastMCP[Any]()

register_asset_set_asset_tools(asset_set_asset_server)
