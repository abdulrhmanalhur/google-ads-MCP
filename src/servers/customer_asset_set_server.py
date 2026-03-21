"""Customer asset set server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.assets.customer_asset_set_service import (
    register_customer_asset_set_tools,
)

customer_asset_set_server = FastMCP[Any]()

register_customer_asset_set_tools(customer_asset_set_server)
