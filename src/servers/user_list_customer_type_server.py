"""User list customer type server module."""

from typing import Any

from fastmcp import FastMCP

from src.services.audiences.user_list_customer_type_service import (
    register_user_list_customer_type_tools,
)

user_list_customer_type_server = FastMCP[Any]()

register_user_list_customer_type_tools(user_list_customer_type_server)
