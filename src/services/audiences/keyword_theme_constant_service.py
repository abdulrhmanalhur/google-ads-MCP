"""Keyword theme constant service implementation (read-only)."""

from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastmcp import Context, FastMCP
from google.ads.googleads.errors import GoogleAdsException
from google.ads.googleads.v20.services.services.keyword_theme_constant_service import (
    KeywordThemeConstantServiceClient,
)
from google.ads.googleads.v20.services.types.keyword_theme_constant_service import (
    SuggestKeywordThemeConstantsRequest,
    SuggestKeywordThemeConstantsResponse,
)

from src.sdk_client import get_sdk_client
from src.utils import get_logger, serialize_proto_message

logger = get_logger(__name__)


class KeywordThemeConstantService:
    """Service for keyword theme constants (read-only)."""

    def __init__(self) -> None:
        """Initialize the service."""
        self._client: Optional[KeywordThemeConstantServiceClient] = None

    @property
    def client(self) -> KeywordThemeConstantServiceClient:
        """Get the service client."""
        if self._client is None:
            sdk_client = get_sdk_client()
            self._client = sdk_client.client.get_service("KeywordThemeConstantService")
        assert self._client is not None
        return self._client

    async def suggest_keyword_theme_constants(
        self,
        ctx: Context,
        query_text: str,
        country_code: str = "US",
        language_code: str = "en",
    ) -> Dict[str, Any]:
        """Suggest keyword theme constants for Smart campaigns.

        Args:
            ctx: FastMCP context
            query_text: The keyword theme query text
            country_code: ISO-3166 two-letter country code (default: US)
            language_code: Two-letter language code (default: en)

        Returns:
            Keyword theme constant suggestions
        """
        try:
            request = SuggestKeywordThemeConstantsRequest()
            request.query_text = query_text
            request.country_code = country_code
            request.language_code = language_code

            response: SuggestKeywordThemeConstantsResponse = (
                self.client.suggest_keyword_theme_constants(request=request)
            )

            await ctx.log(
                level="info",
                message=f"Retrieved keyword theme constants for query: {query_text}",
            )

            return serialize_proto_message(response)

        except GoogleAdsException as e:
            error_msg = f"Google Ads API error: {e.failure}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e
        except Exception as e:
            error_msg = f"Failed to suggest keyword theme constants: {str(e)}"
            await ctx.log(level="error", message=error_msg)
            raise Exception(error_msg) from e


def create_keyword_theme_constant_tools(
    service: KeywordThemeConstantService,
) -> List[Callable[..., Awaitable[Any]]]:
    """Create tool functions for keyword theme constant service."""
    tools = []

    async def suggest_keyword_theme_constants(
        ctx: Context,
        query_text: str,
        country_code: str = "US",
        language_code: str = "en",
    ) -> Dict[str, Any]:
        """Suggest keyword theme constants for Smart campaigns.

        Args:
            query_text: The keyword theme query text (e.g., 'plumber', 'roofer')
            country_code: ISO-3166 two-letter country code (default: US)
            language_code: Two-letter language code (default: en)

        Returns:
            List of suggested keyword theme constants with display names and resource names
        """
        return await service.suggest_keyword_theme_constants(
            ctx=ctx,
            query_text=query_text,
            country_code=country_code,
            language_code=language_code,
        )

    tools.append(suggest_keyword_theme_constants)
    return tools


def register_keyword_theme_constant_tools(
    mcp: FastMCP[Any],
) -> KeywordThemeConstantService:
    """Register keyword theme constant tools with the MCP server."""
    service = KeywordThemeConstantService()
    tools = create_keyword_theme_constant_tools(service)
    for tool in tools:
        mcp.tool(tool)
    return service
