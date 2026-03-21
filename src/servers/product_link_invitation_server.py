"""Product link invitation server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.product_integration.product_link_invitation_service import (
    register_product_link_invitation_tools,
)

product_link_invitation_server = FastMCP[Any]()

register_product_link_invitation_tools(product_link_invitation_server)
