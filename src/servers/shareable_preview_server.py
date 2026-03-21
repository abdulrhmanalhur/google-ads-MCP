"""Shareable preview server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.campaign.shareable_preview_service import (
    register_shareable_preview_tools,
)

shareable_preview_server = FastMCP[Any]()

register_shareable_preview_tools(shareable_preview_server)
