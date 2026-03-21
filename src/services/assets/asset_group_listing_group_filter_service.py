"""Asset group listing group filter service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.listing_group_filter_type_enum import (
    ListingGroupFilterTypeEnum,
)
from google.ads.googleads.v20.resources.types.asset_group_listing_group_filter import (
    AssetGroupListingGroupFilter,
)
from google.ads.googleads.v20.services.services.asset_group_listing_group_filter_service import (
    AssetGroupListingGroupFilterServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.asset_group_listing_group_filter_service import (
    AssetGroupListingGroupFilterOperation,
    MutateAssetGroupListingGroupFiltersRequest,
    MutateAssetGroupListingGroupFiltersResponse,
)
from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class AssetGroupListingGroupFilterService:
    """Service for managing asset group listing group filters (Performance Max)."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[AssetGroupListingGroupFilterServiceClient] = None

    @property
    def client(self) -> AssetGroupListingGroupFilterServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "AssetGroupListingGroupFilterService"
            )
        assert self._client is not None
        return self._client

    async def create_listing_group_filter(
        self,
        ctx: Context,
        customer_id: str,
        asset_group_id: str,
        filter_type: ListingGroupFilterTypeEnum.ListingGroupFilterType,
        parent_listing_group_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an asset group listing group filter.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_group_id: The asset group ID
            filter_type: Type of listing group filter (UNIT, SUBDIVISION)
            parent_listing_group_filter: Optional resource name of parent filter

        Returns:
            Created filter details
        """
        try:
            customer_id = format_customer_id(customer_id)
            asset_group_resource = (
                f"customers/{customer_id}/assetGroups/{asset_group_id}"
            )

            listing_group_filter = AssetGroupListingGroupFilter()
            listing_group_filter.asset_group = asset_group_resource
            listing_group_filter.type_ = filter_type

            if parent_listing_group_filter:
                listing_group_filter.parent_listing_group_filter = (
                    parent_listing_group_filter
                )

            operation = AssetGroupListingGroupFilterOperation()
            operation.create = listing_group_filter

            request = MutateAssetGroupListingGroupFiltersRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response: MutateAssetGroupListingGroupFiltersResponse = (
                self.client.mutate_asset_group_listing_group_filters(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Created listing group filter for asset group {asset_group_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create listing group filter: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_listing_group_filter(
        self,
        ctx: Context,
        customer_id: str,
        asset_group_id: str,
        listing_group_filter_id: str,
    ) -> Dict[str, Any]:
        """Remove an asset group listing group filter.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_group_id: The asset group ID
            listing_group_filter_id: The listing group filter ID

        Returns:
            Removal result
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = f"customers/{customer_id}/assetGroupListingGroupFilters/{asset_group_id}~{listing_group_filter_id}"

            operation = AssetGroupListingGroupFilterOperation()
            operation.remove = resource_name

            request = MutateAssetGroupListingGroupFiltersRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_asset_group_listing_group_filters(
                request=request
            )

            await ctx.log(
                level="info",
                message=f"Removed listing group filter {listing_group_filter_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove listing group filter: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_listing_group_filters(
        self,
        ctx: Context,
        customer_id: str,
        asset_group_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List asset group listing group filters.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_group_id: Optional asset group ID to filter by
            limit: Maximum number of results

        Returns:
            List of listing group filters
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    asset_group_listing_group_filter.resource_name,
                    asset_group_listing_group_filter.id,
                    asset_group_listing_group_filter.asset_group,
                    asset_group_listing_group_filter.type,
                    asset_group_listing_group_filter.listing_source,
                    asset_group_listing_group_filter.parent_listing_group_filter
                FROM asset_group_listing_group_filter
            """

            conditions = []
            if asset_group_id:
                asset_group_resource = (
                    f"customers/{customer_id}/assetGroups/{asset_group_id}"
                )
                conditions.append(
                    f"asset_group_listing_group_filter.asset_group = '{asset_group_resource}'"
                )

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += f" LIMIT {limit}"

            response = google_ads_service.search(customer_id=customer_id, query=query)

            filters = []
            for row in response:
                f = row.asset_group_listing_group_filter
                filters.append(
                    {
                        "resource_name": f.resource_name,
                        "id": str(f.id),
                        "asset_group": f.asset_group,
                        "type": f.type_.name if f.type_ else "UNKNOWN",
                        "listing_source": f.listing_source.name
                        if f.listing_source
                        else "UNKNOWN",
                        "parent_listing_group_filter": f.parent_listing_group_filter,
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(filters)} listing group filters",
            )

            return filters

        except Exception as e:
            error_msg = f"Failed to list listing group filters: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_asset_group_listing_group_filter_tools(
    service: AssetGroupListingGroupFilterService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for asset group listing group filter service."""
    tools = []

    async def create_listing_group_filter(
        ctx: Context,
        customer_id: str,
        asset_group_id: str,
        filter_type: str = "UNIT_INCLUDED",
        parent_listing_group_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create an asset group listing group filter for Performance Max campaigns.

        Args:
            customer_id: The customer ID
            asset_group_id: The asset group ID
            filter_type: Type of filter - UNIT_INCLUDED, UNIT_EXCLUDED, or SUBDIVISION
            parent_listing_group_filter: Optional resource name of parent filter

        Returns:
            Created listing group filter details
        """
        filter_type_enum = getattr(
            ListingGroupFilterTypeEnum.ListingGroupFilterType, filter_type
        )
        return await service.create_listing_group_filter(
            ctx=ctx,
            customer_id=customer_id,
            asset_group_id=asset_group_id,
            filter_type=filter_type_enum,
            parent_listing_group_filter=parent_listing_group_filter,
        )

    async def remove_listing_group_filter(
        ctx: Context,
        customer_id: str,
        asset_group_id: str,
        listing_group_filter_id: str,
    ) -> Dict[str, Any]:
        """Remove an asset group listing group filter.

        Args:
            customer_id: The customer ID
            asset_group_id: The asset group ID
            listing_group_filter_id: The listing group filter ID

        Returns:
            Removal result
        """
        return await service.remove_listing_group_filter(
            ctx=ctx,
            customer_id=customer_id,
            asset_group_id=asset_group_id,
            listing_group_filter_id=listing_group_filter_id,
        )

    async def list_listing_group_filters(
        ctx: Context,
        customer_id: str,
        asset_group_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List asset group listing group filters.

        Args:
            customer_id: The customer ID
            asset_group_id: Optional asset group ID to filter by
            limit: Maximum number of results

        Returns:
            List of listing group filters
        """
        return await service.list_listing_group_filters(
            ctx=ctx,
            customer_id=customer_id,
            asset_group_id=asset_group_id,
            limit=limit,
        )

    tools.extend(
        [
            create_listing_group_filter,
            remove_listing_group_filter,
            list_listing_group_filters,
        ]
    )
    return tools


def register_asset_group_listing_group_filter_tools(
    mcp: FastMCP[Any],
) -> AssetGroupListingGroupFilterService:
    """Register asset group listing group filter tools with the MCP server."""
    service = AssetGroupListingGroupFilterService()
    tools = create_asset_group_listing_group_filter_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
