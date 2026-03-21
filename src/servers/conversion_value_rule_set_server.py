"""Conversion value rule set server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.conversions.conversion_value_rule_set_service import (
    register_conversion_value_rule_set_tools,
)

conversion_value_rule_set_server = FastMCP[Any]()

register_conversion_value_rule_set_tools(conversion_value_rule_set_server)
