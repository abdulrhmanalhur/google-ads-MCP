"""Third party app analytics link service implementation."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.services.services.google_ads_service import (
    GoogleAdsServiceClient,
)
from google.ads.googleads.v20.services.services.third_party_app_analytics_link_service import (
    ThirdPartyAppAnalyticsLinkServiceClient,
)
from google.ads.googleads.v20.services.types.third_party_app_analytics_link_service import (
    RegenerateShareableLinkIdRequest,
    RegenerateShareableLinkIdResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class ThirdPartyAppAnalyticsLinkService:
    """Service for managing third party app analytics links."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[ThirdPartyAppAnalyticsLinkServiceClient] = None

    @property
    def client(self) -> ThirdPartyAppAnalyticsLinkServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "ThirdPartyAppAnalyticsLinkService"
            )
        assert self._client is not None
        return self._client

    async def regenerate_shareable_link_id(
        self,
        ctx: Context,
        customer_id: str,
        account_link_id: str,
    ) -> Dict[str, Any]:
        """Regenerate the shareable link ID for a third party app analytics link.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            account_link_id: The account link ID

        Returns:
            Regenerated link details
        """
        try:
            customer_id = format_customer_id(customer_id)
            resource_name = (
                f"customers/{customer_id}/thirdPartyAppAnalyticsLinks/{account_link_id}"
            )

            request = RegenerateShareableLinkIdRequest()
            request.resource_name = resource_name

            response: RegenerateShareableLinkIdResponse = (
                self.client.regenerate_shareable_link_id(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Regenerated shareable link ID for analytics link {account_link_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to regenerate shareable link ID: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def list_third_party_app_analytics_links(
        self,
        ctx: Context,
        customer_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List third party app analytics links.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            limit: Maximum number of results

        Returns:
            List of third party app analytics links
        """
        try:
            customer_id = format_customer_id(customer_id)

            sdk_client = get_sdk_client()
            google_ads_service: GoogleAdsServiceClient = sdk_client.client.get_service(
                "GoogleAdsService"
            )

            query = f"""
                SELECT
                    third_party_app_analytics_link.resource_name,
                    third_party_app_analytics_link.shareable_link_id
                FROM third_party_app_analytics_link
                LIMIT {limit}
            """

            response = google_ads_service.search(customer_id=customer_id, query=query)

            links = []
            for row in response:
                link = row.third_party_app_analytics_link
                links.append(
                    {
                        "resource_name": link.resource_name,
                        "shareable_link_id": link.shareable_link_id,
                    }
                )

            await ctx.log(
                level="info",
                message=f"Found {len(links)} third party app analytics links",
            )

            return links

        except Exception as e:
            error_msg = f"Failed to list third party app analytics links: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_third_party_app_analytics_link_tools(
    service: ThirdPartyAppAnalyticsLinkService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for third party app analytics link service."""
    tools = []

    async def regenerate_shareable_link_id(
        ctx: Context,
        customer_id: str,
        account_link_id: str,
    ) -> Dict[str, Any]:
        """Regenerate the shareable link ID for a third party app analytics link.

        The regenerated link ID should be provided to the third party
        when setting up app analytics tracking.

        Args:
            customer_id: The customer ID
            account_link_id: The account link ID

        Returns:
            Regenerated shareable link details
        """
        return await service.regenerate_shareable_link_id(
            ctx=ctx,
            customer_id=customer_id,
            account_link_id=account_link_id,
        )

    async def list_third_party_app_analytics_links(
        ctx: Context,
        customer_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List third party app analytics links.

        Args:
            customer_id: The customer ID
            limit: Maximum number of results

        Returns:
            List of third party app analytics links with shareable link IDs
        """
        return await service.list_third_party_app_analytics_links(
            ctx=ctx,
            customer_id=customer_id,
            limit=limit,
        )

    tools.extend(
        [
            regenerate_shareable_link_id,
            list_third_party_app_analytics_links,
        ]
    )
    return tools


def register_third_party_app_analytics_link_tools(
    mcp: FastMCP[Any],
) -> ThirdPartyAppAnalyticsLinkService:
    """Register third party app analytics link tools with the MCP server."""
    service = ThirdPartyAppAnalyticsLinkService()
    tools = create_third_party_app_analytics_link_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
