"""User list customer type service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.user_list_customer_type_category import (
    UserListCustomerTypeCategoryEnum,
)
from google.ads.googleads.v20.resources.types.user_list_customer_type import (
    UserListCustomerType,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.services.user_list_customer_type_service import (
    UserListCustomerTypeServiceClient,
)
from google.ads.googleads.v20.services.types.user_list_customer_type_service import (
    MutateUserListCustomerTypesRequest,
    MutateUserListCustomerTypesResponse,
    UserListCustomerTypeOperation,
)

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class UserListCustomerTypeService:
    """Service for managing user list customer types."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[UserListCustomerTypeServiceClient] = None

    @property
    def client(self) -> UserListCustomerTypeServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("UserListCustomerTypeService")
        assert self._client is not None
        return self._client

    async def create_user_list_customer_type(
        self,
        ctx: Context,
        customer_id: str,
        user_list_id: str,
        customer_type_category: UserListCustomerTypeCategoryEnum.UserListCustomerTypeCategory,
    ) -> Dict[str, Any]:
        """Attach a customer type to a user list.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            user_list_id: The user list ID
            customer_type_category: The customer type category

        Returns:
            Created user list customer type details
        """
        try:
            customer_id = format_customer_id(customer_id)
            user_list_resource = f"customers/{customer_id}/userLists/{user_list_id}"

            user_list_customer_type = UserListCustomerType()
            user_list_customer_type.user_list = user_list_resource
            user_list_customer_type.customer_type_category = customer_type_category

            operation = UserListCustomerTypeOperation()
            operation.create = user_list_customer_type

            request = MutateUserListCustomerTypesRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response: MutateUserListCustomerTypesResponse = (
                self.client.mutate_user_list_customer_types(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created user list customer type for user list {user_list_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create user list customer type: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_user_list_customer_type(
        self,
        ctx: Context,
        customer_id: str,
        user_list_id: str,
        customer_type_category: str,
    ) -> Dict[str, Any]:
        """Remove a customer type from a user list.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            user_list_id: The user list ID
            customer_type_category: The customer type category string

        Returns:
            Removal result
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/userListCustomerTypes/{user_list_id}~{customer_type_category}"

            operation = UserListCustomerTypeOperation()
            operation.remove = resource_name

            request = MutateUserListCustomerTypesRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_user_list_customer_types(request=request)

            await ctx.log(
                level="info",
                message=f"Removed customer type from user list {user_list_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove user list customer type: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_user_list_customer_types(
        self,
        ctx: Context,
        customer_id: str,
        user_list_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List user list customer types.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            user_list_id: Optional user list ID to filter by
            limit: Maximum number of results

        Returns:
            List of user list customer types
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    user_list_customer_type.resource_name,
                    user_list_customer_type.user_list,
                    user_list_customer_type.customer_type_category
                FROM user_list_customer_type
            """

            conditions = []
            if user_list_id:
                user_list_resource = f"customers/{customer_id}/userLists/{user_list_id}"
                conditions.append(
                    f"user_list_customer_type.user_list = '{user_list_resource}'"
                )

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" LIMIT {limit}"

            response = google_ads_service.search(customer_id=customer_id, query=query)

            types = []
            for row in response:
                ulct = row.user_list_customer_type
                types.append(
                    {
                        "resource_name": ulct.resource_name,
                        "user_list": ulct.user_list,
                        "customer_type_category": ulct.customer_type_category.name
                        if ulct.customer_type_category
                        else "UNKNOWN",
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(types)} user list customer types",
            )

            return types

        except Exception as e:
            error_msg = f"Failed to list user list customer types: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_user_list_customer_type_tools(
    service: UserListCustomerTypeService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for user list customer type service."""
    tools = []

    async def create_user_list_customer_type(
        ctx: Context,
        customer_id: str,
        user_list_id: str,
        customer_type_category: str,
    ) -> Dict[str, Any]:
        """Attach a customer type category to a user list.

        Args:
            customer_id: The customer ID
            user_list_id: The user list ID
            customer_type_category: Customer type category such as PURCHASERS,
                ALL_VISITORS, HIGH_VALUE_CUSTOMERS, LIFE_TIME_VALUE_SIMILAR,
                SIMILAR_VISITORS

        Returns:
            Created user list customer type details
        """
        category_enum = getattr(
            UserListCustomerTypeCategoryEnum.UserListCustomerTypeCategory,
            customer_type_category,
        )
        return await service.create_user_list_customer_type(
            ctx=ctx,
            customer_id=customer_id,
            user_list_id=user_list_id,
            customer_type_category=category_enum,
        )

    async def remove_user_list_customer_type(
        ctx: Context,
        customer_id: str,
        user_list_id: str,
        customer_type_category: str,
    ) -> Dict[str, Any]:
        """Remove a customer type from a user list.

        Args:
            customer_id: The customer ID
            user_list_id: The user list ID
            customer_type_category: The customer type category to remove

        Returns:
            Removal result
        """
        return await service.remove_user_list_customer_type(
            ctx=ctx,
            customer_id=customer_id,
            user_list_id=user_list_id,
            customer_type_category=customer_type_category,
        )

    async def list_user_list_customer_types(
        ctx: Context,
        customer_id: str,
        user_list_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List customer types associated with user lists.

        Args:
            customer_id: The customer ID
            user_list_id: Optional user list ID to filter by
            limit: Maximum number of results

        Returns:
            List of user list customer types
        """
        return await service.list_user_list_customer_types(
            ctx=ctx,
            customer_id=customer_id,
            user_list_id=user_list_id,
            limit=limit,
        )

    tools.extend(
        [
            create_user_list_customer_type,
            remove_user_list_customer_type,
            list_user_list_customer_types,
        ]
    )
    return tools


def register_user_list_customer_type_tools(
    mcp: FastMCP[Any],
) -> UserListCustomerTypeService:
    """Register user list customer type tools with the MCP server."""
    service = UserListCustomerTypeService()
    tools = create_user_list_customer_type_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
