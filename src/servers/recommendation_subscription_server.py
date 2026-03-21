"""Recommendation subscription server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.planning.recommendation_subscription_service import (
    register_recommendation_subscription_tools,
)

recommendation_subscription_server = FastMCP[Any]()

register_recommendation_subscription_tools(recommendation_subscription_server)
