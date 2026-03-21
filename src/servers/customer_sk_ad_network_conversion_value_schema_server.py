"""Customer SK Ad Network conversion value schema server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.conversions.customer_sk_ad_network_conversion_value_schema_service import (
    register_customer_sk_ad_network_conversion_value_schema_tools,
)

customer_sk_ad_network_conversion_value_schema_server = FastMCP[Any]()

register_customer_sk_ad_network_conversion_value_schema_tools(
    customer_sk_ad_network_conversion_value_schema_server
)
