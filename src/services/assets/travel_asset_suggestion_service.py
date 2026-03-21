"""Travel asset suggestion service implementation (read-only)."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.services.services.travel_asset_suggestion_service import (
    TravelAssetSuggestionServiceClient,
)
from google.ads.googleads.v20.services.types.travel_asset_suggestion_service import (
    SuggestTravelAssetsRequest,
    SuggestTravelAssetsResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import format_customer_id, get_logger, serialize_proto_message

logger = get_logger(__name__)


class TravelAssetSuggestionService:
    """Service for getting travel-specific asset suggestions."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[TravelAssetSuggestionServiceClient] = None

    @property
    def client(self) -> TravelAssetSuggestionServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("TravelAssetSuggestionService")
        assert self._client is not None
        return self._client

    async def suggest_travel_assets(
        self,
        ctx: Context,
        customer_id: str,
        language_option: str,
        place_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get travel asset suggestions for hotel campaigns.

        Args:
            ctx: FastMCP context
            customer_id: The customer ID
            language_option: Language code for suggestions (e.g., 'en-US')
            place_ids: Optional list of Google place IDs for hotels

        Returns:
            Travel asset suggestions including text and image assets
        """
        try:
            customer_id = format_customer_id(customer_id)

            request = SuggestTravelAssetsRequest()
            request.customer_id = customer_id
            request.language_option = language_option

            if place_ids:
                request.place_ids.extend(place_ids)

            response: SuggestTravelAssetsResponse = self.client.suggest_travel_assets(
                request=request
            )

            await ctx.log(
                level="info",
                message=f"Retrieved travel asset suggestions for customer {customer_id}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to get travel asset suggestions: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_travel_asset_suggestion_tools(
    service: TravelAssetSuggestionService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for travel asset suggestion service."""
    tools = []

    async def suggest_travel_assets(
        ctx: Context,
        customer_id: str,
        language_option: str,
        place_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get travel asset suggestions for hotel campaigns.

        Args:
            customer_id: The customer ID
            language_option: Language code for suggestions (e.g., 'en-US')
            place_ids: Optional list of Google place IDs for specific hotels

        Returns:
            Travel asset suggestions including hotel text and image assets
        """
        return await service.suggest_travel_assets(
            ctx=ctx,
            customer_id=customer_id,
            language_option=language_option,
            place_ids=place_ids,
        )

    tools.append(suggest_travel_assets)
    return tools


def register_travel_asset_suggestion_tools(
    mcp: FastMCP[Any],
) -> TravelAssetSuggestionService:
    """Register travel asset suggestion tools with the MCP server."""
    service = TravelAssetSuggestionService()
    tools = create_travel_asset_suggestion_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
