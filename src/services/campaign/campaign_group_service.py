"""Campaign group service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.enums.types.campaign_group_status import (
    CampaignGroupStatusEnum,
)
from google.ads.googleads.v20.resources.types.campaign_group import CampaignGroup
from google.ads.googleads.v20.services.services.campaign_group_service import (
    CampaignGroupServiceClient,
)
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.types.campaign_group_service import (
    CampaignGroupOperation,
    MutateCampaignGroupsRequest,
    MutateCampaignGroupsResponse,
)
from google.protobuf import field_mask_pb2

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class CampaignGroupService:
    """Service for managing campaign groups."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[CampaignGroupServiceClient] = None

    @property
    def client(self) -> CampaignGroupServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("CampaignGroupService")
        assert self._client is not None
        return self._client

    async def create_campaign_group(
        self,
        ctx: Context,
        customer_id: str,
        name: str,
        status: CampaignGroupStatusEnum.CampaignGroupStatus = CampaignGroupStatusEnum.CampaignGroupStatus.ENABLED,
    ) -> Dict[str, Any]:
        """Create a campaign group.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            name: Campaign group name
            status: Campaign group status (ENABLED or REMOVED)

        Returns:
            Created campaign group details
        """
        try:
            customer_id = format_customer_id(customer_id)

            campaign_group = CampaignGroup()
            campaign_group.name = name
            campaign_group.status = status

            operation = CampaignGroupOperation()
            operation.create = campaign_group

            request = MutateCampaignGroupsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response: MutateCampaignGroupsResponse = self.client.mutate_campaign_groups(
                request=request
            )

            await ctx.log(
                level="info",
                message=f"Created campaign group '{name}'",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to create campaign group: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def update_campaign_group(
        self,
        ctx: Context,
        customer_id: str,
        campaign_group_id: str,
        name: Optional[str] = None,
        status: Optional[CampaignGroupStatusEnum.CampaignGroupStatus] = None,
    ) -> Dict[str, Any]:
        """Update a campaign group.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_group_id: The campaign group ID
            name: Optional new name
            status: Optional new status

        Returns:
            Updated campaign group details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/campaignGroups/{campaign_group_id}"
            )

            campaign_group = CampaignGroup()
            campaign_group.resource_name = resource_name

            update_mask_paths = []

            if name is not None:
                campaign_group.name = name
                update_mask_paths.append("name")

            if status is not None:
                campaign_group.status = status
                update_mask_paths.append("status")

            operation = CampaignGroupOperation()
            operation.update = campaign_group
            operation.update_mask.CopyFrom(
                field_mask_pb2.FieldMask(paths=update_mask_paths)
            )

            request = MutateCampaignGroupsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_campaign_groups(request=request)

            await ctx.log(
                level="info",
                message=f"Updated campaign group {campaign_group_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to update campaign group: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def remove_campaign_group(
        self,
        ctx: Context,
        customer_id: str,
        campaign_group_id: str,
    ) -> Dict[str, Any]:
        """Remove a campaign group.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            campaign_group_id: The campaign group ID to remove

        Returns:
            Removal result
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/campaignGroups/{campaign_group_id}"
            )

            operation = CampaignGroupOperation()
            operation.remove = resource_name

            request = MutateCampaignGroupsRequest()
            request.customer_id = customer_id
            request.operations = [operation]

            response = self.client.mutate_campaign_groups(request=request)

            await ctx.log(
                level="info",
                message=f"Removed campaign group {campaign_group_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to remove campaign group: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_campaign_groups(
        self,
        ctx: Context,
        customer_id: str,
        include_removed: bool = False,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List campaign groups.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            include_removed: Whether to include removed groups
            limit: Maximum number of results

        Returns:
            List of campaign groups
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = """
                SELECT
                    campaign_group.resource_name,
                    campaign_group.id,
                    campaign_group.name,
                    campaign_group.status
                FROM campaign_group
            """

            if not include_removed:
                query += " WHERE campaign_group.status != 'REMOVED'"

            query += f" ORDER BY campaign_group.id DESC LIMIT {limit}"

            response = google_ads_service.search(customer_id=customer_id, query=query)

            groups = []
            for row in response:
                g = row.campaign_group
                groups.append(
                    {
                        "resource_name": g.resource_name,
                        "id": str(g.id),
                        "name": g.name,
                        "status": g.status.name if g.status else "UNKNOWN",
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(groups)} campaign groups",
            )

            return groups

        except Exception as e:
            error_msg = f"Failed to list campaign groups: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_campaign_group_tools(
    service: CampaignGroupService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for campaign group service."""
    tools = []

    async def create_campaign_group(
        ctx: Context,
        customer_id: str,
        name: str,
        status: str = "ENABLED",
    ) -> Dict[str, Any]:
        """Create a campaign group to organize campaigns.

        Args:
            customer_id: The customer ID
            name: Campaign group name
            status: Status - ENABLED or REMOVED

        Returns:
            Created campaign group details
        """
        status_enum = getattr(CampaignGroupStatusEnum.CampaignGroupStatus, status)
        return await service.create_campaign_group(
            ctx=ctx,
            customer_id=customer_id,
            name=name,
            status=status_enum,
        )

    async def update_campaign_group(
        ctx: Context,
        customer_id: str,
        campaign_group_id: str,
        name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a campaign group.

        Args:
            customer_id: The customer ID
            campaign_group_id: The campaign group ID
            name: Optional new name
            status: Optional new status - ENABLED or REMOVED

        Returns:
            Updated campaign group details
        """
        status_enum = (
            getattr(CampaignGroupStatusEnum.CampaignGroupStatus, status)
            if status
            else None
        )
        return await service.update_campaign_group(
            ctx=ctx,
            customer_id=customer_id,
            campaign_group_id=campaign_group_id,
            name=name,
            status=status_enum,
        )

    async def remove_campaign_group(
        ctx: Context,
        customer_id: str,
        campaign_group_id: str,
    ) -> Dict[str, Any]:
        """Remove a campaign group.

        Args:
            customer_id: The customer ID
            campaign_group_id: The campaign group ID to remove

        Returns:
            Removal result
        """
        return await service.remove_campaign_group(
            ctx=ctx,
            customer_id=customer_id,
            campaign_group_id=campaign_group_id,
        )

    async def list_campaign_groups(
        ctx: Context,
        customer_id: str,
        include_removed: bool = False,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List campaign groups.

        Args:
            customer_id: The customer ID
            include_removed: Whether to include removed groups
            limit: Maximum number of results

        Returns:
            List of campaign groups
        """
        return await service.list_campaign_groups(
            ctx=ctx,
            customer_id=customer_id,
            include_removed=include_removed,
            limit=limit,
        )

    tools.extend(
        [
            create_campaign_group,
            update_campaign_group,
            remove_campaign_group,
            list_campaign_groups,
        ]
    )
    return tools


def register_campaign_group_tools(mcp: FastMCP[Any]) -> CampaignGroupService:
    """Register campaign group tools with the MCP server."""
    service = CampaignGroupService()
    tools = create_campaign_group_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
