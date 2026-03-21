"""Asset set asset service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.resources.types.asset_set_asset import AssetSetAsset
from google.ads.googleads.v20.services.services.asset_set_asset_service import (
    AssetSetAssetServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.asset_set_asset_service import (
    AssetSetAssetOperation,
    MutateAssetSetAssetsRequest,
    MutateAssetSetAssetsResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class AssetSetAssetService:
    """Service for managing assets within asset sets."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[AssetSetAssetServiceClient] = None

    @property
    def client(self) -> AssetSetAssetServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("AssetSetAssetService")
        assert self._client is not None
        return self._client

    async def create_asset_set_asset(
        self,
        ctx: Context,
        customer_id: str,
        asset_set_id: str,
        asset_id: str,
    ) -> Dict[str, Any]:
        """Link an asset to an asset set.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_set_id: The asset set ID
            asset_id: The asset ID to link

        Returns:
            Created asset set asset details
        """
        try:
            customer_id = format_customer_id(customer_id)
            asset_set_resource = f"customers/{customer_id}/assetSets/{asset_set_id}"
            asset_resource = f"customers/{customer_id}/assets/{asset_id}"

            asset_set_asset = AssetSetAsset()
            asset_set_asset.asset_set = asset_set_resource
            asset_set_asset.asset = asset_resource

            operation = AssetSetAssetOperation()
            operation.create = asset_set_asset

            request = MutateAssetSetAssetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response: MutateAssetSetAssetsResponse = (
                self.client.mutate_asset_set_assets(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Linked asset {asset_id} to asset set {asset_set_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create asset set asset: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_asset_set_asset(
        self,
        ctx: Context,
        customer_id: str,
        asset_set_id: str,
        asset_id: str,
    ) -> Dict[str, Any]:
        """Remove an asset from an asset set.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_set_id: The asset set ID
            asset_id: The asset ID to remove

        Returns:
            Removal result
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/assetSetAssets/{asset_set_id}~{asset_id}"
            )

            operation = AssetSetAssetOperation()
            operation.remove = resource_name

            request = MutateAssetSetAssetsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_asset_set_assets(request=request)

            await ctx.log(
                level="info",
                message=f"Removed asset {asset_id} from asset set {asset_set_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove asset set asset: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_asset_set_assets(
        self,
        ctx: Context,
        customer_id: str,
        asset_set_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List assets within asset sets.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            asset_set_id: Optional asset set ID to filter by
            limit: Maximum number of results

        Returns:
            List of asset set assets
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    asset_set_asset.resource_name,
                    asset_set_asset.asset_set,
                    asset_set_asset.asset,
                    asset_set_asset.status
                FROM asset_set_asset
            """

            conditions = []
            if asset_set_id:
                asset_set_resource = f"customers/{customer_id}/assetSets/{asset_set_id}"
                conditions.append(f"asset_set_asset.asset_set = '{asset_set_resource}'")
            conditions.append("asset_set_asset.status != 'REMOVED'")

            query += " WHERE " + " AND ".join(conditions)
            query += f" LIMIT {limit}"

            response = google_ads_service.search(customer_id=customer_id, query=query)

            assets = []
            for row in response:
                asa = row.asset_set_asset
                assets.append(
                    {
                        "resource_name": asa.resource_name,
                        "asset_set": asa.asset_set,
                        "asset": asa.asset,
                        "status": asa.status.name if asa.status else "UNKNOWN",
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(assets)} asset set assets",
            )

            return assets

        except Exception as e:
            error_msg = f"Failed to list asset set assets: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_asset_set_asset_tools(
    service: AssetSetAssetService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for asset set asset service."""
    tools = []

    async def create_asset_set_asset(
        ctx: Context,
        customer_id: str,
        asset_set_id: str,
        asset_id: str,
    ) -> Dict[str, Any]:
        """Link an asset to an asset set.

        Args:
            customer_id: The customer ID
            asset_set_id: The asset set ID
            asset_id: The asset ID to link to the asset set

        Returns:
            Created link details
        """
        return await service.create_asset_set_asset(
            ctx=ctx,
            customer_id=customer_id,
            asset_set_id=asset_set_id,
            asset_id=asset_id,
        )

    async def remove_asset_set_asset(
        ctx: Context,
        customer_id: str,
        asset_set_id: str,
        asset_id: str,
    ) -> Dict[str, Any]:
        """Remove an asset from an asset set.

        Args:
            customer_id: The customer ID
            asset_set_id: The asset set ID
            asset_id: The asset ID to remove from the asset set

        Returns:
            Removal result
        """
        return await service.remove_asset_set_asset(
            ctx=ctx,
            customer_id=customer_id,
            asset_set_id=asset_set_id,
            asset_id=asset_id,
        )

    async def list_asset_set_assets(
        ctx: Context,
        customer_id: str,
        asset_set_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List assets within asset sets.

        Args:
            customer_id: The customer ID
            asset_set_id: Optional asset set ID to filter by
            limit: Maximum number of results

        Returns:
            List of asset set assets with their status
        """
        return await service.list_asset_set_assets(
            ctx=ctx,
            customer_id=customer_id,
            asset_set_id=asset_set_id,
            limit=limit,
        )

    tools.extend(
        [
            create_asset_set_asset,
            remove_asset_set_asset,
            list_asset_set_assets,
        ]
    )
    return tools


def register_asset_set_asset_tools(mcp: FastMCP[Any]) -> AssetSetAssetService:
    """Register asset set asset tools with the MCP server."""
    service = AssetSetAssetService()
    tools = create_asset_set_asset_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
