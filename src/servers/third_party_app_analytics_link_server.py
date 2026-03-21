"""Third party app analytics link server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.product_integration.third_party_app_analytics_link_service import (
    register_third_party_app_analytics_link_tools,
)

third_party_app_analytics_link_server = FastMCP[Any]()

register_third_party_app_analytics_link_tools(third_party_app_analytics_link_server)
