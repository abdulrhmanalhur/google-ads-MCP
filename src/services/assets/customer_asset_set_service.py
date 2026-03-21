"""Customer asset set service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.resources.types.customer_asset_set import CustomerAssetSet
from google.ads.googleads.v20.services.services.customer_asset_set_service import (
    CustomerAssetSetServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.customer_asset_set_service import (
    CustomerAssetSetOperation,
    MutateCustomerAssetSetsRequest,
    MutateCustomerAssetSetsResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class CustomerAssetSetService:
    """Service for managing customer-level asset sets."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[CustomerAssetSetServiceClient] = None

    @property
    def client(self) -> CustomerAssetSetServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("CustomerAssetSetService")
        assert self._client is not None
        return self._client

    async def create_customer_asset_set(
        self,
        ctx: Context,
        customer_id: str,
        asset_set_id: str,
    ) -> Dict[str, Any]:
        """Link an asset set to a customer.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_set_id: The asset set ID to link

        Returns:
            Created customer asset set details
        """
        try:
            customer_id = format_customer_id(customer_id)
            asset_set_resource = f"customers/{customer_id}/assetSets/{asset_set_id}"

            customer_asset_set = CustomerAssetSet()
            customer_asset_set.asset_set = asset_set_resource

            operation = CustomerAssetSetOperation()
            operation.create = customer_asset_set

            request = MutateCustomerAssetSetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response: MutateCustomerAssetSetsResponse = (
                self.client.mutate_customer_asset_sets(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Linked asset set {asset_set_id} to customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create customer asset set: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_customer_asset_set(
        self,
        ctx: Context,
        customer_id: str,
        asset_set_id: str,
    ) -> Dict[str, Any]:
        """Remove an asset set from a customer.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_set_id: The asset set ID to remove

        Returns:
            Removal result
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/customerAssetSets/{asset_set_id}"

            operation = CustomerAssetSetOperation()
            operation.remove = resource_name

            request = MutateCustomerAssetSetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_customer_asset_sets(request=request)

            await ctx.log(
                level="info",
                message=f"Removed asset set {asset_set_id} from customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove customer asset set: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_customer_asset_sets(
        self,
        ctx: Context,
        customer_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List customer asset sets.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            limit: Maximum number of results

        Returns:
            List of customer asset sets
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = f"""
                SELECT
                    customer_asset_set.resource_name,
                    customer_asset_set.asset_set,
                    customer_asset_set.status
                FROM customer_asset_set
                WHERE customer_asset_set.status != 'REMOVED'
                LIMIT {limit}
            """

            response = google_ads_service.search(customer_id=customer_id, query=query)

            asset_sets = []
            for row in response:
                cas = row.customer_asset_set
                asset_sets.append(
                    {
                        "resource_name": cas.resource_name,
                        "asset_set": cas.asset_set,
                        "status": cas.status.name if cas.status else "UNKNOWN",
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(asset_sets)} customer asset sets",
            )

            return asset_sets

        except Exception as e:
            error_msg = f"Failed to list customer asset sets: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_customer_asset_set_tools(
    service: CustomerAssetSetService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for customer asset set service."""
    tools = []

    async def create_customer_asset_set(
        ctx: Context,
        customer_id: str,
        asset_set_id: str,
    ) -> Dict[str, Any]:
        """Link an asset set to a customer account.

        Args:
            customer_id: The customer ID
            asset_set_id: The asset set ID to link to the customer

        Returns:
            Created customer asset set link details
        """
        return await service.create_customer_asset_set(
            ctx=ctx,
            customer_id=customer_id,
            asset_set_id=asset_set_id,
        )

    async def remove_customer_asset_set(
        ctx: Context,
        customer_id: str,
        asset_set_id: str,
    ) -> Dict[str, Any]:
        """Remove an asset set from a customer account.

        Args:
            customer_id: The customer ID
            asset_set_id: The asset set ID to remove from the customer

        Returns:
            Removal result
        """
        return await service.remove_customer_asset_set(
            ctx=ctx,
            customer_id=customer_id,
            asset_set_id=asset_set_id,
        )

    async def list_customer_asset_sets(
        ctx: Context,
        customer_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List asset sets linked to a customer account.

        Args:
            customer_id: The customer ID
            limit: Maximum number of results

        Returns:
            List of customer asset sets
        """
        return await service.list_customer_asset_sets(
            ctx=ctx,
            customer_id=customer_id,
            limit=limit,
        )

    tools.extend(
        [
            create_customer_asset_set,
            remove_customer_asset_set,
            list_customer_asset_sets,
        ]
    )
    return tools


def register_customer_asset_set_tools(mcp: FastMCP[Any]) -> CustomerAssetSetService:
    """Register customer asset set tools with the MCP server."""
    service = CustomerAssetSetService()
    tools = create_customer_asset_set_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
