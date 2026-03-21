"""Keyword theme constant server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.audiences.keyword_theme_constant_service import (
    register_keyword_theme_constant_tools,
)

keyword_theme_constant_server = FastMCP[Any]()

register_keyword_theme_constant_tools(keyword_theme_constant_server)
