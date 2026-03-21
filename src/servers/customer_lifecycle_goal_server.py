"""Customer lifecycle goal server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.conversions.customer_lifecycle_goal_service import (
    register_customer_lifecycle_goal_tools,
)

customer_lifecycle_goal_server = FastMCP[Any]()

register_customer_lifecycle_goal_tools(customer_lifecycle_goal_server)
