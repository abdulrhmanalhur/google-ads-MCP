"""Content creator insights service implementation (read-only)."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.common.types.criteria import (
    LocationInfo,
    YouTubeChannelInfo,
)
from google.ads.googleads.v20.services.services.content_creator_insights_service import (
    ContentCreatorInsightsServiceClient,
)
from google.ads.googleads.v20.services.types.content_creator_insights_service import (
    GenerateCreatorInsightsRequest,
    GenerateCreatorInsightsResponse,
    GenerateTrendingInsightsRequest,
    GenerateTrendingInsightsResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class ContentCreatorInsightsService:
    """Service for getting YouTube content creator insights."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[ContentCreatorInsightsServiceClient] = None

    @property
    def client(self) -> ContentCreatorInsightsServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service(
                "ContentCreatorInsightsService"
            )
        assert self._client is not None
        return self._client

    async def generate_creator_insights(
        self,
        ctx: Context,
        customer_id: str,
        customer_insights_group: str,
        country_geo_target_constants: List[str],
        youtube_channel_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate insights for YouTube creators.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            customer_insights_group: User-defined name for the customer being planned for
            country_geo_target_constants: List of country geo target constant resource names
            youtube_channel_ids: Optional list of YouTube channel IDs

        Returns:
            Creator insights data
        """
        try:
            customer_id = format_customer_id(customer_id)

            request = GenerateCreatorInsightsRequest()
            request.customer_id = customer_id
            request.customer_insights_group = customer_insights_group

            # Add country locations
            for geo_target in country_geo_target_constants:
                location = LocationInfo()
                location.geo_target_constant = geo_target
                request.country_locations.append(location)

            # Set YouTube channels search if provided
            if youtube_channel_ids:
                channels = GenerateCreatorInsightsRequest.YouTubeChannels()
                for channel_id in youtube_channel_ids:
                    channel_info = YouTubeChannelInfo()
                    channel_info.channel_id = channel_id
                    channels.youtube_channels.append(channel_info)
                request.search_channels = channels

            response: GenerateCreatorInsightsResponse = (
                self.client.generate_creator_insights(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Generated creator insights for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate creator insights: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e

    async def generate_trending_insights(
        self,
        ctx: Context,
        customer_id: str,
        customer_insights_group: str,
        country_geo_target_constants: List[str],
    ) -> Dict[str, Any]:
        """Generate trending content insights for YouTube.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            customer_insights_group: User-defined name for the customer being planned for
            country_geo_target_constants: List of country geo target constant resource names

        Returns:
            Trending content insights
        """
        try:
            customer_id = format_customer_id(customer_id)

            request = GenerateTrendingInsightsRequest()
            request.customer_id = customer_id
            request.customer_insights_group = customer_insights_group

            for geo_target in country_geo_target_constants:
                location = LocationInfo()
                location.geo_target_constant = geo_target
                request.country_locations.append(location)

            response: GenerateTrendingInsightsResponse = (
                self.client.generate_trending_insights(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Generated trending insights for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to generate trending insights: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_content_creator_insights_tools(
    service: ContentCreatorInsightsService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for content creator insights service."""
    tools = []

    async def generate_creator_insights(
        ctx: Context,
        customer_id: str,
        customer_insights_group: str,
        country_geo_target_constants: List[str],
        youtube_channel_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate insights for YouTube creators.

        Args:
            customer_id: The customer ID
            customer_insights_group: Name for the customer being planned for
            country_geo_target_constants: List of country geo target resource names
                (e.g., 'geoTargetConstants/2840' for US)
            youtube_channel_ids: Optional list of YouTube channel IDs to get insights for

        Returns:
            Creator insights including metrics and audience data
        """
        return await service.generate_creator_insights(
            ctx=ctx,
            customer_id=customer_id,
            customer_insights_group=customer_insights_group,
            country_geo_target_constants=country_geo_target_constants,
            youtube_channel_ids=youtube_channel_ids,
        )

    async def generate_trending_insights(
        ctx: Context,
        customer_id: str,
        customer_insights_group: str,
        country_geo_target_constants: List[str],
    ) -> Dict[str, Any]:
        """Generate trending content insights for YouTube.

        Args:
            customer_id: The customer ID
            customer_insights_group: Name for the customer being planned for
            country_geo_target_constants: List of country geo target resource names

        Returns:
            Trending content insights including trending topics and creators
        """
        return await service.generate_trending_insights(
            ctx=ctx,
            customer_id=customer_id,
            customer_insights_group=customer_insights_group,
            country_geo_target_constants=country_geo_target_constants,
        )

    tools.extend(
        [
            generate_creator_insights,
            generate_trending_insights,
        ]
    )
    return tools


def register_content_creator_insights_tools(
    mcp: FastMCP[Any],
) -> ContentCreatorInsightsService:
    """Register content creator insights tools with the MCP server."""
    service = ContentCreatorInsightsService()
    tools = create_content_creator_insights_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
