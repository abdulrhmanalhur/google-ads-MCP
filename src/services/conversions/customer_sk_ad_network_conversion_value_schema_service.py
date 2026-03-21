"""Customer SK Ad Network conversion value schema service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.resources.types.customer_sk_ad_network_conversion_value_schema import (
    CustomerSkAdNetworkConversionValueSchema,
)
from google.ads.googleads.v20.services.services.customer_sk_ad_network_conversion_value_schema_service import (
    CustomerSkAdNetworkConversionValueSchemaServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.customer_sk_ad_network_conversion_value_schema_service import (
    CustomerSkAdNetworkConversionValueSchemaOperation,
    MutateCustomerSkAdNetworkConversionValueSchemaRequest,
    MutateCustomerSkAdNetworkConversionValueSchemaResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class CustomerSkAdNetworkConversionValueSchemaService:
    """Service for managing SK Ad Network conversion value schemas."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[
            CustomerSkAdNetworkConversionValueSchemaServiceClient
        ] = None

    @property
    def client(self) -> CustomerSkAdNetworkConversionValueSchemaServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "CustomerSkAdNetworkConversionValueSchemaService"
            )
        assert self._client is not None
        return self._client

    async def update_sk_ad_network_schema(
        self,
        ctx: Context,
        customer_id: str,
        account_link_id: str,
        schema: CustomerSkAdNetworkConversionValueSchema,
    ) -> Dict[str, Any]:
        """Update a SK Ad Network conversion value schema.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            account_link_id: The account link ID
            schema: The schema to update

        Returns:
            Updated schema details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/customerSkAdNetworkConversionValueSchemas/{account_link_id}"

            schema.resource_name = resource_name

            operation = CustomerSkAdNetworkConversionValueSchemaOperation()
            operation.update = schema

            request = MutateCustomerSkAdNetworkConversionValueSchemaRequest()
            request.customer_id = customer_id
            request.operation = operation

            response: MutateCustomerSkAdNetworkConversionValueSchemaResponse = (
                self.client.mutate_customer_sk_ad_network_conversion_value_schema(
                    request=request
                )
            )

            await ctx.log(
                level="info",
                message=f"Updated SK Ad Network schema for account link {account_link_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update SK Ad Network schema: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_sk_ad_network_schemas(
        self,
        ctx: Context,
        customer_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List SK Ad Network conversion value schemas.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            limit: Maximum number of results

        Returns:
            List of SK Ad Network schemas
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = f"""
                SELECT
                    customer_sk_ad_network_conversion_value_schema.resource_name
                FROM customer_sk_ad_network_conversion_value_schema
                LIMIT {limit}
            """

            response = google_ads_service.search(customer_id=customer_id, query=query)

            schemas = []
            for row in response:
                s = row.customer_sk_ad_network_conversion_value_schema
                schemas.append(
                    {
                        "resource_name": s.resource_name,
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(schemas)} SK Ad Network schemas",
            )

            return schemas

        except Exception as e:
            error_msg = f"Failed to list SK Ad Network schemas: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_customer_sk_ad_network_conversion_value_schema_tools(
    service: CustomerSkAdNetworkConversionValueSchemaService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for SK Ad Network conversion value schema service."""
    tools = []

    async def list_sk_ad_network_schemas(
        ctx: Context,
        customer_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List SK Ad Network conversion value schemas.

        These schemas define how iOS app conversion values map to Google Ads events.

        Args:
            customer_id: The customer ID
            limit: Maximum number of results

        Returns:
            List of SK Ad Network conversion value schemas
        """
        return await service.list_sk_ad_network_schemas(
            ctx=ctx,
            customer_id=customer_id,
            limit=limit,
        )

    tools.append(list_sk_ad_network_schemas)
    return tools


def register_customer_sk_ad_network_conversion_value_schema_tools(
    mcp: FastMCP[Any],
) -> CustomerSkAdNetworkConversionValueSchemaService:
    """Register SK Ad Network schema tools with the MCP server."""
    service = CustomerSkAdNetworkConversionValueSchemaService()
    tools = create_customer_sk_ad_network_conversion_value_schema_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
